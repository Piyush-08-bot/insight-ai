const axios = require('axios');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

class AIService {
    /**
     * Analyze a project using the AI service
     */
    static async analyzeProject(projectPath, userId, fileTypes = ['.py', '.js']) {
        try {
            const response = await axios.post(`${AI_SERVICE_URL}/api/analyze`, {
                project_path: projectPath,
                file_types: fileTypes
            }, {
                timeout: 300000
            });
            return response.data;
        } catch (error) {
            if (error.response) {
                throw new Error(`AI Service Error: ${error.response.data.detail || error.response.statusText}`);
            } else if (error.code === 'ECONNREFUSED') {
                throw new Error('AI Service is not running. Please start it on port 8000.');
            } else {
                throw new Error(`Failed to connect to AI Service: ${error.message}`);
            }
        }
    }

    /**
     * Query the codebase (single question, no memory)
     */
    static async query(projectId, question) {
        try {
            const response = await axios.post(`${AI_SERVICE_URL}/api/query`, {
                project_id: projectId,
                question: question,
            }, { timeout: 60000 });
            return response.data;
        } catch (error) {
            if (error.response) {
                throw new Error(`AI Service Error: ${error.response.data.detail || error.response.statusText}`);
            }
            throw new Error(`Failed to query AI Service: ${error.message}`);
        }
    }

    /**
     * Chat with codebase (with memory)
     */
    static async chat(projectId, question, sessionId = null) {
        try {
            const response = await axios.post(`${AI_SERVICE_URL}/api/chat`, {
                project_id: projectId,
                question: question,
                session_id: sessionId,
            }, { timeout: 60000 });
            return response.data;
        } catch (error) {
            if (error.response) {
                throw new Error(`AI Service Error: ${error.response.data.detail || error.response.statusText}`);
            }
            throw new Error(`Failed to chat with AI Service: ${error.message}`);
        }
    }

    /**
     * Run specialized analysis
     */
    static async runAnalysis(projectId, analysisType) {
        try {
            const response = await axios.post(`${AI_SERVICE_URL}/api/analysis`, {
                project_id: projectId,
                analysis_type: analysisType,
            }, { timeout: 120000 });
            return response.data;
        } catch (error) {
            if (error.response) {
                throw new Error(`AI Service Error: ${error.response.data.detail || error.response.statusText}`);
            }
            throw new Error(`Failed to run analysis: ${error.message}`);
        }
    }

    /**
     * Clear chat session
     */
    static async clearChatSession(sessionId) {
        try {
            const response = await axios.delete(`${AI_SERVICE_URL}/api/chat/${sessionId}`);
            return response.data;
        } catch (error) {
            console.error(`Error clearing session: ${error.message}`);
            return null;
        }
    }

    /**
     * Delete a project
     */
    static async deleteProject(projectId) {
        try {
            const response = await axios.delete(`${AI_SERVICE_URL}/api/projects/${projectId}`);
            return response.data;
        } catch (error) {
            console.error(`Error deleting project from AI service: ${error.message}`);
            return null;
        }
    }

    /**
     * Health check
     */
    static async healthCheck() {
        try {
            const response = await axios.get(`${AI_SERVICE_URL}/health`, { timeout: 5000 });
            return response.data;
        } catch (error) {
            return { status: 'unhealthy', error: error.message };
        }
    }
}

module.exports = AIService;
