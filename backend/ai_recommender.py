import os
from typing import List, Dict
import httpx

class AIRecommender:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("<<key>>")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_recommendations(self, failed_checks: List[Dict]) -> List[Dict]:
        """Generate AI recommendations for failed checks"""
        if not failed_checks:
            return []
        
        # If no API key, return fallback recommendations
        if not self.api_key:
            return self._generate_fallback_recommendations(failed_checks)
        
        try:
            # Prepare prompt for AI
            failed_list = "\n".join([
                f"- {check['check']}: {check['details']}"
                for check in failed_checks
            ])
            
            prompt = f"""You are an accessibility expert. The following web compliance checks have failed:

{failed_list}

For each failed check, provide a specific, actionable recommendation to fix the issue. 
Keep each recommendation to 2-3 sentences, focused on practical implementation.
Format your response as a numbered list matching the order of failed checks above."""

            # Call Groq API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-70b-versatile",  # Free model
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert in web accessibility and WCAG guidelines."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                
                # Parse AI response
                recommendations = self._parse_ai_response(ai_response, failed_checks)
                return recommendations
            
        except Exception as e:
            print(f"AI recommendation error: {str(e)}")
            return self._generate_fallback_recommendations(failed_checks)
    
    def _parse_ai_response(self, response: str, failed_checks: List[Dict]) -> List[Dict]:
        """Parse AI response into structured recommendations"""
        lines = response.strip().split('\n')
        recommendations = []
        current_rec = ""
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                if current_rec:
                    recommendations.append(current_rec)
                # Remove numbering
                current_rec = line.lstrip('0123456789.-) ')
            elif line:
                current_rec += " " + line
        
        if current_rec:
            recommendations.append(current_rec)
        
        # Match recommendations with failed checks
        result = []
        for i, check in enumerate(failed_checks):
            rec = recommendations[i] if i < len(recommendations) else self._get_fallback_for_check(check['check'])
            result.append({
                "check": check['check'],
                "recommendation": rec
            })
        
        return result
    
    def _generate_fallback_recommendations(self, failed_checks: List[Dict]) -> List[Dict]:
        """Generate fallback recommendations when AI is unavailable"""
        return [
            {
                "check": check['check'],
                "recommendation": self._get_fallback_for_check(check['check'])
            }
            for check in failed_checks
        ]
    
    def _get_fallback_for_check(self, check_name: str) -> str:
        """Get predefined recommendation for a check"""
        fallback_recs = {
            "Meaningful Sequence": "Ensure proper heading hierarchy (h1, h2, h3) without skipping levels. Use semantic HTML elements in a logical order that makes sense when read by screen readers.",
            
            "Sensory Characteristics": "Avoid instructions that rely solely on sensory characteristics like color, shape, or position. Include text descriptions alongside visual cues (e.g., 'Submit button (green)' instead of 'green button').",
            
            "Use of Colour": "Don't use color as the only way to convey information. Add text labels, icons, or patterns alongside color indicators. For required fields, use asterisks (*) or the word 'required' in addition to color.",
            
            "Keyboard Accessible": "Ensure all interactive elements (buttons, links, forms) are accessible via keyboard. Add tabindex and proper event handlers to custom interactive elements. Avoid using click handlers on non-interactive elements like divs or spans.",
            
            "No Keyboard Trap": "Ensure users can navigate away from all interactive components using only the keyboard. Modals and dialogs should have a clear close button accessible via Tab and Enter/Escape keys.",
            
            "Pointer Cancellation": "For drag-and-drop or complex pointer interactions, provide an undo mechanism or confirmation step. Use 'onclick' instead of 'onmousedown' to allow users to cancel actions by moving the pointer away.",
            
            "Label in Name": "Ensure the visible text label of a form element matches or is contained within its accessible name (aria-label). If a button shows 'Submit', its aria-label should include the word 'Submit'.",
            
            "Timing Adjustable": "If your page has timeouts or auto-refresh, provide controls to extend, adjust, or disable the time limit. Display a warning before timeouts with an option to extend the session.",
            
            "Seizures": "Avoid content that flashes more than 3 times per second. Remove or slow down blinking, flashing, or strobing animations. Use CSS animations with slower, smoother transitions.",
            
            "Bypass Blocks": "Add a 'Skip to main content' link at the top of your page that allows keyboard users to bypass repetitive navigation. The link should be one of the first focusable elements and point to an element with id='main' or similar."
        }
        
        return fallback_recs.get(check_name, "Review this check and implement accessibility best practices according to WCAG 2.1 guidelines.")