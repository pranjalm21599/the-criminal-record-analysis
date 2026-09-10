// Small shared helpers for shaping API data into Cytoscape/graph-friendly shapes.

export function toCytoscapeElements(nodes = [], edges = [], colorMap = {}) {
  const cyNodes = nodes.map(n => ({
    data: {
      id: String(n.id || n.name),
      label: n.name || n.id,
      type: n.label || 'Unknown',
      color: colorMap[n.label] || '#8A94A3',
    }
  }));
  const cyEdges = edges.map((e, i) => ({
    data: { id: `e-${i}`, source: String(e.source), target: String(e.target), label: e.type || '' }
  }));
  return [...cyNodes, ...cyEdges];
}
