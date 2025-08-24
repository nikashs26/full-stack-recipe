# Full-Stack Recipe App

A modern recipe management application with AI-powered meal planning, built with React + TypeScript frontend and Flask + Python backend.

## 🚀 Live Demo

- **Frontend**: [Netlify](https://your-app-name.netlify.app) (update with your actual URL)
- **Backend**: [Railway](https://your-app-name-production.up.railway.app) (update with your actual URL)

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **Netlify** for hosting

### Backend
- **Flask** Python web framework
- **ChromaDB** for vector storage and recipe search
- **Railway** for hosting
- **Docker** for containerization

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/full-stack-recipe.git
   cd full-stack-recipe
   ```

2. **Frontend Setup**
   ```bash
   npm install
   npm run dev
   ```
   Frontend will be available at `http://localhost:8081`

3. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
   Backend will be available at `http://localhost:5003`

## 🌐 Deployment

### Free Deployment Setup

This app is configured for **completely free deployment** using:
- **Railway** (backend) - 500 hours/month free
- **Netlify** (frontend) - 100GB bandwidth/month free

📖 **Complete deployment guide**: [RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md)

### Quick Deploy Steps

1. **Backend (Railway)**
   - Connect GitHub repo to Railway
   - Set source directory to `backend`
   - Add environment variables
   - Deploy

2. **Frontend (Netlify)**
   - Connect GitHub repo to Netlify
   - Set build command: `npm run build`
   - Set publish directory: `dist`
   - Add backend URL environment variable
   - Deploy

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```bash
FLASK_SECRET_KEY=your-secret-key
DEBUG=false
```

**Frontend (.env.local)**
```bash
VITE_BACKEND_URL=http://localhost:5003
```

## 📱 Features

- 🍳 Recipe management and search
- 🤖 AI-powered meal planning
- 📱 Responsive design
- 🔐 User authentication
- 📁 Recipe organization
- 🛒 Shopping list generation
- 📊 Nutritional information
- 🌍 International cuisine support

## 🚨 Troubleshooting

### Common Issues

1. **Railway crashes**: Check memory usage (free tier: 512MB)
2. **Frontend can't connect**: Verify CORS settings and backend URL
3. **Build failures**: Check Node.js version and dependencies

### Health Checks

Test your Railway backend:
```bash
cd backend
python health_check.py https://your-railway-url.up.railway.app
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

- **Railway**: [Discord](https://discord.gg/railway)
- **Netlify**: [Community](https://community.netlify.com)
- **GitHub Issues**: For code-specific problems

---

**Happy Cooking! 👨‍🍳**
