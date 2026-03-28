const express = require('express');
const router = express.Router();
const Project = require('../models/Project');
const AIService = require('../services/aiService');
const auth = require('../middleware/auth');

// Get all projects for user
router.get('/', auth, async (req, res) => {
    try {
        const projects = await Project.find({ userId: req.user.id })
            .sort({ createdAt: -1 });

        res.json(projects);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get single project
router.get('/:id', auth, async (req, res) => {
    try {
        const project = await Project.findOne({
            _id: req.params.id,
            userId: req.user.id
        });

        if (!project) {
            return res.status(404).json({ error: 'Project not found' });
        }

        res.json(project);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Analyze a new project
router.post('/analyze', auth, async (req, res) => {
    try {
        const { projectPath, name, fileTypes } = req.body;

        // Create project in database
        const project = await Project.create({
            userId: req.user.id,
            name: name || projectPath.split('/').pop(),
            path: projectPath,
            fileTypes: fileTypes || ['.py', '.js', '.ts'],
            status: 'analyzing'
        });

        // Call AI service (async - don't wait)
        AIService.analyzeProject(projectPath, req.user.id, project.fileTypes)
            .then(async (aiResult) => {
                // Update project with AI results
                project.aiProjectId = aiResult.project_id;
                project.status = 'completed';
                project.stats = {
                    documentsCount: aiResult.documents_count,
                    chunksCount: aiResult.chunks_count,
                    analyzedAt: new Date()
                };
                await project.save();
            })
            .catch(async (error) => {
                console.error('AI Analysis failed:', error);
                project.status = 'failed';
                await project.save();
            });

        // Return immediately with pending status
        res.status(202).json({
            message: 'Analysis started',
            project: project
        });

    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Delete project
router.delete('/:id', auth, async (req, res) => {
    try {
        const project = await Project.findOne({
            _id: req.params.id,
            userId: req.user.id
        });

        if (!project) {
            return res.status(404).json({ error: 'Project not found' });
        }

        // Delete from AI service
        if (project.aiProjectId) {
            await AIService.deleteProject(project.aiProjectId);
        }

        // Delete from database
        await project.remove();

        res.json({ message: 'Project deleted successfully' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
