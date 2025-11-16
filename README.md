# Aurora Quest ✨

Your AI-powered learning companion that transforms study sessions into interactive adventures!

## 🎯 Features

- **AI-Generated Quizzes** - Personalized quizzes from your study materials
- **Smart Flashcards** - Automatic flashcard creation
- **Language Learning** - Conversational AI tutors
- **Progress Tracking** - Gamified learning experience
- **Document Upload** - Support for PDF text extraction
- **Chat with Notes** - Ask questions about your uploaded materials

## 🚀 Deployment on Vercel

### Quick Deploy

1. **Fork this repository** to your GitHub account
2. **Import to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Git Repository"
   - Connect your GitHub and select this repo
   - Vercel will automatically detect the Python setup

3. **Configure Environment Variables** (Optional for AI features):
   - In Vercel dashboard, go to your project → Settings → Environment Variables
   - Add: `GEMINI_API_KEY` with your Google AI Studio API key

4. **Deploy!** Your app will be live at `your-project.vercel.app`

### File Structure

```
Aurora Quest/
├── api/
│   └── main.py          # FastAPI serverless function
├── index.html           # Frontend (served from memory)
├── vercel.json          # Vercel deployment configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn api.main:app --reload

# Visit http://localhost:8000
```

## 🔧 API Endpoints

- `GET /` - Homepage
- `GET /api/health` - Health check
- `POST /api/upload-notes` - Upload PDF/text files
- `POST /api/generate-quiz` - Create AI-generated quizzes
- `POST /api/chat` - Chat with your notes
- `POST /api/language-tutor` - Practice languages
- `GET /api/performance-dashboard` - View progress stats

## 📱 Usage

1. **Visit your deployed app URL**
2. **Upload study materials** (PDF or text files)
3. **Generate quizzes** or **ask questions**
4. **Track your progress** with the dashboard

## ⚙️ Environment Variables

- `GEMINI_API_KEY` - Google Gemini AI API key (optional, enables AI features)

## 🏗️ Technologies Used

- **Backend**: FastAPI (Python)
- **AI**: Google Generative AI (Gemini)
- **Deployment**: Vercel (Serverless)
- **File Processing**: PyPDF2 for PDFs

## 📚 AI Features (With API Key)

- Quiz generation
- Flashcard creation
- Language tutoring
- Document chat/analysis

---

**Made with ❤️ using FastAPI and Vercel. Transform your learning experience! ✨**
