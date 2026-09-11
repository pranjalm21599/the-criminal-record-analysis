import axios from 'axios';

// Service addresses. Defaults are the local ports from the team's service map;
// override any of them via a .env file (see .env.example) without touching code.
const env = import.meta.env ?? {};

const BACKEND_URL = env.VITE_BACKEND_URL || 'http://localhost:8000';    // Member 1
const NLP_URL = env.VITE_NLP_URL || 'http://localhost:8001';            // Member 2
const GRAPH_URL = env.VITE_GRAPH_URL || 'http://localhost:8002';        // Member 3
const ANALYSIS_URL = env.VITE_ANALYSIS_URL || 'http://localhost:8003';  // Member 4
const AI_URL = env.VITE_AI_URL || 'http://localhost:8004';              // Member 6

const backendApi = axios.create({ baseURL: BACKEND_URL, timeout: 30000 });
const nlpApi = axios.create({ baseURL: NLP_URL, timeout: 15000 });
const graphApi = axios.create({ baseURL: GRAPH_URL, timeout: 10000 });
const analysisApi = axios.create({ baseURL: ANALYSIS_URL, timeout: 10000 });
const aiApi = axios.create({ baseURL: AI_URL, timeout: 30000 });

export const api = {
  // Cases (Member 1)
  getCases: () => backendApi.get('/cases/'),
  getCase: (id) => backendApi.get(`/cases/${id}`),
  getCaseSummary: (id) => backendApi.get(`/cases/${id}/summary`),
  createCase: (data) => backendApi.post('/cases/', data),

  // Upload (Member 1)
  uploadFIR: (formData) => backendApi.post('/upload/fir', formData),
  uploadCallRecords: (formData) => backendApi.post('/upload/call-records', formData),
  uploadTransactions: (formData) => backendApi.post('/upload/transactions', formData),

  // NLP (Member 2)
  extractEntities: (text) => nlpApi.post('/extract/text', { text }),

  // Graph (Member 3)
  getPersonNetwork: (name, depth = 2) =>
    graphApi.get(`/graph/person/${encodeURIComponent(name)}/network`, { params: { depth } }),
  searchGraph: (query) => graphApi.get('/graph/search', { params: { q: query } }),
  getShortestPath: (p1, p2) =>
    graphApi.get('/graph/shortest-path', { params: { person1: p1, person2: p2 } }),
  getGraphStats: () => graphApi.get('/graph/stats'),

  // Analysis (Member 4)
  getCentrality: () => analysisApi.get('/analysis/centrality'),
  getCommunities: () => analysisApi.get('/analysis/communities'),
  getTransactionAnomalies: () => analysisApi.get('/analysis/anomalies/transactions'),
  getCommunicationAnomalies: () => analysisApi.get('/analysis/anomalies/calls'),
  getRiskScores: () => analysisApi.get('/analysis/risk/all'),
  runFullAnalysis: () => analysisApi.post('/analysis/run-full-analysis'),

  // AI Chat (Member 6)
  sendChatMessage: (message, conversationId = 'default', caseId = null) =>
    aiApi.post('/chat/', { message, conversation_id: conversationId, case_id: caseId }),
  askQuestion: (question, caseId = null) =>
    aiApi.post('/chat/ask', { question, case_id: caseId }),
  resetChat: (conversationId = 'default') =>
    aiApi.post('/chat/reset', null, { params: { conversation_id: conversationId } }),
  getSampleQuestions: () => aiApi.get('/chat/sample-questions'),
};
