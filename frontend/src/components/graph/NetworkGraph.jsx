import { useEffect, useRef, useState } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import { Loader2, AlertCircle, Maximize2 } from 'lucide-react';
import { api } from '../../api/apiClient';

try { cytoscape.use(coseBilkent); } catch (e) { /* already registered */ }

const NODE_COLORS = {
  Person: '#4C9AFF',
  Phone: '#27C93F',
  Vehicle: '#F5A623',
  Location: '#B57BEE',
  Organization: '#E5484D',
  BankAccount: '#2DD4BF',
  Case: '#8A94A3',
  FIR: '#F2C94C',
};

export default function NetworkGraph({ personName, onNodeClick }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (personName) loadNetwork(personName);
  }, [personName]);

  const loadNetwork = async (name, depth = 2) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getPersonNetwork(name, depth);
      const data = response.data;

      const cytoscapeNodes = (data.nodes || []).map(node => ({
        data: {
          id: String(node.id || node.name),
          label: node.name || node.id,
          type: node.label || 'Unknown',
          color: NODE_COLORS[node.label] || '#8A94A3',
          size: node.label === 'Person' ? 46 : 28,
        }
      }));

      const cytoscapeEdges = (data.edges || []).map((edge, i) => ({
        data: {
          id: `edge-${i}`,
          source: String(edge.source),
          target: String(edge.target),
          label: edge.type || '',
        }
      }));

      setGraphData({ nodes: cytoscapeNodes, edges: cytoscapeEdges });
    } catch (err) {
      // Distinguish "that name isn't in the graph" from "the service is down".
      // Blaming the service for a simple no-match sends people off restarting
      // containers when they just need a different name.
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 404) {
        const suggestions = detail?.did_you_mean;
        setError(
          suggestions?.length
            ? `No one matching "${name}" in the graph. Try: ${suggestions.slice(0, 5).join(', ')}`
            : `No one matching "${name}" in the graph. Upload evidence first, or try another name.`
        );
      } else if (status === 503) {
        setError('The Graph service cannot reach Neo4j. Check: docker compose logs neo4j');
      } else {
        setError('Could not reach the Graph service (port 8002). Start it, or run docker compose up.');
      }
    } finally {
      setLoading(false);
    }
  };

  const stylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': 'data(color)',
        'label': 'data(label)',
        'font-size': 10,
        'font-family': 'IBM Plex Mono, monospace',
        'color': '#E4E9F0',
        'text-valign': 'bottom',
        'text-margin-y': 6,
        'width': 'data(size)',
        'height': 'data(size)',
        'border-width': 2,
        'border-color': '#0A0E14',
        'transition-property': 'border-width, border-color',
        'transition-duration': 150,
      }
    },
    {
      selector: 'node:selected, node.hovered',
      style: { 'border-width': 3, 'border-color': '#4C9AFF' }
    },
    {
      selector: 'edge',
      style: {
        'width': 1.4,
        'line-color': '#2A3644',
        'target-arrow-color': '#2A3644',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 0.8,
        'curve-style': 'bezier',
        'font-size': 8,
        'font-family': 'IBM Plex Mono, monospace',
        'color': '#6B7684',
        'label': 'data(label)',
        'text-rotation': 'autorotate',
      }
    }
  ];

  return (
    <div className="bg-base-surface rounded-lg border border-base-border overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-base-border">
        <div className="flex items-center gap-2">
          <span className="text-ink-primary font-medium text-sm">Network Graph</span>
          {personName && (
            <span className="font-mono text-[11px] text-signal bg-signal/10 px-2 py-0.5 rounded">
              {personName}
            </span>
          )}
        </div>
        <div className="hidden lg:flex items-center gap-3">
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <span key={type} className="flex items-center gap-1.5 text-[11px] text-ink-faint">
              <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: color }} />
              {type}
            </span>
          ))}
        </div>
      </div>

      <div className="relative" style={{ height: '520px' }}>
        {loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-signal text-sm z-10 bg-base-surface/80">
            <Loader2 size={20} className="animate-spin" />
            Loading network…
          </div>
        )}

        {!loading && error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-ink-muted text-sm px-8 text-center">
            <AlertCircle size={20} className="text-risk-high" />
            {error}
          </div>
        )}

        {!loading && !error && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 text-ink-faint text-sm">
            <Maximize2 size={18} />
            Search a name above to explore the network
          </div>
        )}

        {!loading && !error && graphData.nodes.length > 0 && (
          <CytoscapeComponent
            elements={[...graphData.nodes, ...graphData.edges]}
            stylesheet={stylesheet}
            layout={{ name: 'cose-bilkent', idealEdgeLength: 110, nodeRepulsion: 6500, animate: true, animationDuration: 400 }}
            style={{ width: '100%', height: '100%' }}
            cy={(cy) => {
              cyRef.current = cy;
              cy.off('tap mouseover mouseout');
              cy.on('tap', 'node', (evt) => {
                const node = evt.target;
                onNodeClick?.({ id: node.data('id'), label: node.data('label'), type: node.data('type') });
              });
              cy.on('mouseover', 'node', (evt) => {
                evt.target.addClass('hovered');
                setHoveredNode(evt.target.data());
              });
              cy.on('mouseout', 'node', (evt) => {
                evt.target.removeClass('hovered');
                setHoveredNode(null);
              });
            }}
          />
        )}

        {hoveredNode && (
          <div className="absolute bottom-3 left-3 bg-base-raised border border-base-border rounded-md px-3 py-2 text-xs font-mono text-ink-primary shadow-lg pointer-events-none">
            <div className="text-ink-faint">{hoveredNode.type}</div>
            <div>{hoveredNode.label}</div>
          </div>
        )}
      </div>
    </div>
  );
}
