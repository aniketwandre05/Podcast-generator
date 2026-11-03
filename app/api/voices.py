import base64
import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import VoicePreviewRequest
from app.models.voice_profile import VoiceProfile
from app.sarvam.tts import synthesize_chunk

router = APIRouter(prefix="/api", tags=["voices"])

# Catalog of verified Bulbul voices from official docs
VOICE_CATALOG = [
    # Male voices
    {"id": "shubh", "name": "Shubh", "gender": "male", "description": "Crisp, dynamic, authoritative host", "model": "bulbul:v3"},
    {"id": "rohan", "name": "Rohan", "gender": "male", "description": "Conversational, youthful, engaging co-host", "model": "bulbul:v3"},
    {"id": "aditya", "name": "Aditya", "gender": "male", "description": "Warm, intellectual, expert tone", "model": "bulbul:v3"},
    {"id": "kabir", "name": "Kabir", "gender": "male", "description": "Deep, resonant, storytelling narrator", "model": "bulbul:v3"},
    {"id": "dev", "name": "Dev", "gender": "male", "description": "Casual, friendly, interview guest", "model": "bulbul:v3"},
    {"id": "amit", "name": "Amit", "gender": "male", "description": "Articulate, professional broadcaster", "model": "bulbul:v3"},
    
    # Female voices
    {"id": "priya", "name": "Priya", "gender": "female", "description": "Energetic, bright, charismatic host", "model": "bulbul:v3"},
    {"id": "simran", "name": "Simran", "gender": "female", "description": "Warm, relatable, conversational partner", "model": "bulbul:v3"},
    {"id": "kavya", "name": "Kavya", "gender": "female", "description": "Expressive, insightful, tech & culture", "model": "bulbul:v3"},
    {"id": "ritu", "name": "Ritu", "gender": "female", "description": "Calm, narrative, storytelling voice", "model": "bulbul:v3"},
    {"id": "pooja", "name": "Pooja", "gender": "female", "description": "Clear, informative, news anchor tone", "model": "bulbul:v3"},
    {"id": "ishita", "name": "Ishita", "gender": "female", "description": "Spirited, engaging, interview specialist", "model": "bulbul:v3"},
]

LANGUAGES = [
    {"code": "en-IN", "name": "English (India)"},
    {"code": "hi-IN", "name": "Hindi (हिंदी)"},
    {"code": "bn-IN", "name": "Bengali (বাংলা)"},
    {"code": "ta-IN", "name": "Tamil (தமிழ்)"},
    {"code": "te-IN", "name": "Telugu (తెలుగు)"},
    {"code": "kn-IN", "name": "Kannada (ಕನ್ನಡ)"},
    {"code": "ml-IN", "name": "Malayalam (മലയാളം)"},
    {"code": "mr-IN", "name": "Marathi (मराठी)"},
    {"code": "gu-IN", "name": "Gujarati (ગુજરાતી)"},
    {"code": "pa-IN", "name": "Punjabi (ਪੰਜਾਬੀ)"},
    {"code": "od-IN", "name": "Odia (ଓଡ଼ିଆ)"},
]

LANGUAGE_PREVIEW_TEXTS = {
    "en-IN": "Welcome to PodcastAI! This is a preview of my voice powered by Sarvam Bulbul.",
    "hi-IN": "नमस्ते! पॉडकास्ट एआई में आपका स्वागत है। यह बुलबुल की आवाज़ का प्रीव्यू है।",
    "bn-IN": "নমস্কার! পডকাস্ট এআই-তে আপনাদের স্বাগত। এটি বুলবুল কণ্ঠস্বরের প্রিভিউ।",
    "ta-IN": "வணக்கம்! போட்காஸ்ட் ஏஐ-க்கு உங்களை வரவேற்கிறோம். இது புல்புல் குரலின் முன்னோட்டம்.",
    "te-IN": "నమస్కారం! పాడ్‌కాస్ట్ ఏఐకి స్వాగతం. ఇది బుల్‌బుల్ స్వర ప్రివ్యూ.",
    "kn-IN": "ನಮಸ್ಕಾರ! ಪಾಡ್‌ಕ್ಯಾಸ್ಟ್ ಎಐಗೆ ಸುಸ್ವಾಗತ. ಇದು ಬುಲ್‌ಬುಲ್ ಧ್ವನಿಯ ಪ್ರಿವ್ಯೂ ಆಗಿದೆ.",
    "ml-IN": "നമസ്കാരം! പോഡ്‌കാസ്റ്റ് എഐയിലേക്ക് സ്വാഗതം. ഇത് ബുൾബുൾ ശബ്ദത്തിന്റെ പ്രിവ്യൂ ആണ്.",
    "mr-IN": "नमस्कार! पॉडकास्ट एआय मध्ये आपले स्वागत आहे. हा बुलबुल आवाजाचा प्रिव्ह्यू आहे.",
    "gu-IN": "નમસ્તે! પોડકાસ્ટ એઆઈમાં આપનું સ્વાગત છે. આ બુલબુલ અવાજનું પ્રિવ્યુ છે.",
    "pa-IN": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਪੋਡਕਾਸਟ ਏਆਈ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ। ਇਹ ਬੁਲਬੁਲ ਆਵਾਜ਼ ਦਾ ਪ੍ਰੀਵਿਊ ਹੈ।",
    "od-IN": "ନମସ୍କାର! ପଡକାଷ୍ଟ ଏଆଇକୁ ଆପଣଙ୍କୁ ସ୍ୱାଗତ। ଏହା ବୁଲବୁଲ କଣ୍ଠସ୍ୱରର ଏକ ଝଲକ।",
}

class VoiceProfileCreate(BaseModel):
    name: str
    voice_id: str
    gender: str = "neutral"
    role_description: str = ""
    language_code: str = "en-IN"
    pace: float = 1.0

@router.get("/voices")
def get_voices():
    return {
        "voices": VOICE_CATALOG,
        "languages": LANGUAGES,
        "models": ["bulbul:v3", "bulbul:v4-flash", "bulbul:v2"],
    }

@router.post("/voices/preview")
async def preview_voice(req: VoicePreviewRequest):
    """Generate a quick 1-sentence audio preview for a selected voice in the target language."""
    sample_text = req.text or LANGUAGE_PREVIEW_TEXTS.get(req.language_code, LANGUAGE_PREVIEW_TEXTS["en-IN"])
    try:
        audio_bytes = await synthesize_chunk(
            text=sample_text,
            voice=req.voice,
            language_code=req.language_code,
            pace=req.pace,
            model=req.model,
        )
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        return {
            "status": "success",
            "voice": req.voice,
            "audio_base64": f"data:audio/wav;base64,{b64_audio}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice preview failed: {e}")

@router.get("/voice-profiles")
def list_voice_profiles(db: Session = Depends(get_db)):
    profiles = db.query(VoiceProfile).order_by(VoiceProfile.created_at.desc()).all()
    return profiles

@router.post("/voice-profiles")
def create_voice_profile(req: VoiceProfileCreate, db: Session = Depends(get_db)):
    profile = VoiceProfile(
        id=str(uuid.uuid4()),
        name=req.name,
        voice_id=req.voice_id,
        gender=req.gender,
        role_description=req.role_description,
        language_code=req.language_code,
        pace=req.pace,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

