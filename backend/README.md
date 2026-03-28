# 🚀 INsight Backend

Node.js + Express + MongoDB backend for INsight platform.

## 🏗️ Architecture

This service handles:
- User authentication (JWT)
- Project management (CRUD)
- Session management
- Integration with AI Service
- Data persistence (MongoDB)

## 📦 Installation

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Configure your environment variables
```

## 🚀 Running

```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start

# Run tests
npm test
```

Server runs on: http://localhost:5000

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - Get all user projects
- `GET /api/projects/:id` - Get single project
- `POST /api/projects/analyze` - Analyze new project
- `DELETE /api/projects/:id` - Delete project

### Chat
- `POST /api/chat` - Send chat message
- `GET /api/chat/history/:projectId` - Get chat history

## 🔧 Configuration

```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/insight
JWT_SECRET=your-secret-key
AI_SERVICE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

## 📁 Project Structure

```
backend/
├── src/
│   ├── routes/           # API routes
│   │   ├── auth.routes.js
│   │   ├── project.routes.js
│   │   └── chat.routes.js
│   ├── models/           # MongoDB schemas
│   │   ├── User.js
│   │   ├── Project.js
│   │   └── ChatHistory.js
│   ├── controllers/      # Business logic
│   ├── services/         # External services
│   │   └── aiService.js  # AI Service client
│   ├── middleware/       # Express middleware
│   │   ├── auth.js       # JWT auth
│   │   └── errorHandler.js
│   ├── config/           # Configuration
│   │   └── database.js   # MongoDB connection
│   └── server.js         # Express app
├── tests/
├── package.json
└── README.md
```

## 🔌 Integration with AI Service

The backend communicates with the Python AI Service:

```javascript
// Example: Analyzing a project
const aiResult = await AIService.analyzeProject(
  '/path/to/code',
  userId,
  ['.py', '.js']
);

// Example: Querying codebase
const answer = await AIService.query(
  projectId,
  "How does authentication work?"
);
```

## 🔐 Authentication

Uses JWT (JSON Web Tokens) for authentication:

```javascript
// Login returns JWT token
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

// Use token in Authorization header
GET /api/projects
Authorization: Bearer <token>
```

## 📊 Database Models

### User
- name, email, password (hashed)
- createdAt

### Project
- userId, name, path
- aiProjectId (from AI service)
- status, fileTypes, stats
- createdAt, updatedAt

### ChatHistory
- projectId, userId
- question, answer, sources
- timestamp

## 🧪 Testing

```bash
npm test
```

## 🐳 Docker

```bash
docker build -t insight-backend .
docker run -p 5000:5000 insight-backend
```

## Tech Stack

- **Express** - Web framework
- **MongoDB** - Database
- **Mongoose** - ODM
- **JWT** - Authentication
- **Bcrypt** - Password hashing
- **Axios** - HTTP client (for AI service)
- **Helmet** - Security
- **Morgan** - Logging
