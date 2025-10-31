from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import httpx
from compliance_checks import ComplianceChecker
from ai_recommender import AIRecommender
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Compliance Checker API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI recommender
ai_recommender = AIRecommender()

class URLRequest(BaseModel):
    url: HttpUrl

class ComplianceResult(BaseModel):
    check: str
    status: str
    details: str
    recommendation: Optional[str] = None

class ComplianceResponse(BaseModel):
    url: str
    score: int
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[ComplianceResult]

@app.get("/")
async def root():
    return {
        "message": "AI-based Web Compliance Checker API",
        "version": "1.0.0",
        "endpoints": {
            "check": "/api/check (POST)",
            "health": "/health (GET)"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "ai_enabled": ai_recommender.client is not None}

@app.post("/api/check", response_model=ComplianceResponse)
async def check_compliance(request: URLRequest):
    """
    Check a webpage for accessibility compliance
    """
    url = str(request.url)
    
    try:
        # Fetch the webpage
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            html_content = response.text
        
        # Run compliance checks
        checker = ComplianceChecker(html_content, url)
        check_results = checker.run_all_checks()
        
        # Calculate score
        total_checks = len(check_results)
        passed = sum(1 for r in check_results if r['status'] == 'pass')
        failed = sum(1 for r in check_results if r['status'] == 'fail')
        score = passed  # Score out of 10
        
        # Get failed checks for AI recommendations
        failed_checks = [r for r in check_results if r['status'] == 'fail']
        
        # Generate AI recommendations
        recommendations = {}
        if failed_checks:
            ai_recs = ai_recommender.generate_recommendations(failed_checks)
            recommendations = {rec['check']: rec['recommendation'] for rec in ai_recs}
        
        # Build final results with recommendations
        final_results = []
        for result in check_results:
            final_results.append({
                "check": result['check'],
                "status": result['status'],
                "details": result['details'],
                "recommendation": recommendations.get(result['check']) if result['status'] == 'fail' else None
            })
        
        return ComplianceResponse(
            url=url,
            score=score,
            total_checks=total_checks,
            passed_checks=passed,
            failed_checks=failed,
            results=final_results
        )
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch URL: HTTP {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
