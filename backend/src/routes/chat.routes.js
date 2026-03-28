/**
 * Chat routes - proxy to AI service chat endpoint.
 */
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const AIService = require('../services/aiService');

// Send a chat message
router.post('/', auth, async (req, res) => {
    try {
        const { projectId, question, sessionId } = req.body;

        if (!projectId || !question) {
            return res.status(400).json({ error: 'projectId and question are required' });
        }

        const result = await AIService.chat(projectId, question, sessionId);
        res.json(result);

    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Clear a chat session
router.delete('/:sessionId', auth, async (req, res) => {
    try {
        const result = await AIService.clearChatSession(req.params.sessionId);
        res.json(result || { message: 'Session cleared' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
