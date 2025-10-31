from bs4 import BeautifulSoup
import re
from typing import Dict, List, Tuple

class ComplianceChecker:
    def __init__(self, html_content: str, url: str):
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.url = url
        self.results = []
    
    def check_meaningful_sequence(self) -> Tuple[bool, str]:
        """Check if heading hierarchy is logical"""
        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            return False, "No heading structure found"
        
        levels = [int(h.name[1]) for h in headings]
        
        # Check for proper hierarchy
        has_h1 = 1 in levels
        skips_levels = any(levels[i] - levels[i-1] > 1 for i in range(1, len(levels)))
        
        if not has_h1:
            return False, "Missing main heading (h1)"
        if skips_levels:
            return False, "Heading hierarchy skips levels"
        
        return True, "Proper heading hierarchy maintained"
    
    def check_sensory_characteristics(self) -> Tuple[bool, str]:
        """Check for text describing visual/sensory elements"""
        issues = []
        
        # Look for problematic phrases in text
        problematic_phrases = [
            r'click the (red|green|blue|yellow) button',
            r'the round button',
            r'listen for the sound',
            r'on the right side',
            r'the square icon'
        ]
        
        text_content = self.soup.get_text().lower()
        for phrase in problematic_phrases:
            if re.search(phrase, text_content):
                issues.append(f"Found sensory-dependent instruction")
        
        if issues:
            return False, "; ".join(issues)
        return True, "No sensory-only instructions detected"
    
    def check_use_of_colour(self) -> Tuple[bool, str]:
        """Check if information relies only on color"""
        issues = []
        
        # Check for required fields with only color indicators
        required_fields = self.soup.find_all(['input', 'select', 'textarea'], {'required': True})
        for field in required_fields:
            label = self._find_label_for_input(field)
            if label and '*' not in label.get_text() and 'required' not in label.get_text().lower():
                issues.append(f"Required field may rely only on color indication")
                break
        
        # Check for error messages that might be color-only
        error_elements = self.soup.find_all(class_=re.compile(r'error|danger|alert', re.I))
        if error_elements and not any('error' in elem.get_text().lower() or 'required' in elem.get_text().lower() for elem in error_elements):
            issues.append("Potential color-only error indicators")
        
        if issues:
            return False, "; ".join(issues[:1])  # Report first issue
        return True, "Information not solely dependent on color"
    
    def check_keyboard_accessible(self) -> Tuple[bool, str]:
        """Check for keyboard accessibility features"""
        issues = []
        
        # Check for interactive elements without proper attributes
        interactive = self.soup.find_all(['button', 'a', 'input', 'select', 'textarea'])
        
        # Check for onclick on non-interactive elements
        non_interactive_with_click = self.soup.find_all(
            lambda tag: tag.name in ['div', 'span', 'img', 'p'] and tag.get('onclick')
        )
        
        if non_interactive_with_click:
            issues.append(f"Found {len(non_interactive_with_click)} non-interactive elements with click handlers")
        
        # Check for missing tabindex on custom interactive elements
        custom_buttons = self.soup.find_all(attrs={'role': 'button'})
        for btn in custom_buttons:
            if not btn.get('tabindex') and btn.name not in ['button', 'a']:
                issues.append("Custom interactive elements missing tabindex")
                break
        
        if issues:
            return False, "; ".join(issues)
        return True, "Interactive elements appear keyboard accessible"
    
    def check_no_keyboard_trap(self) -> Tuple[bool, str]:
        """Check for potential keyboard traps"""
        # Look for modal/dialog elements
        modals = self.soup.find_all(attrs={'role': ['dialog', 'alertdialog']})
        
        issues = []
        for modal in modals:
            # Check if modal has close mechanism
            has_close = modal.find(['button', 'a'], text=re.compile(r'close|×|cancel', re.I))
            if not has_close:
                issues.append("Modal/dialog without clear close mechanism")
                break
        
        # Check for elements that might trap focus
        tabindex_negative = self.soup.find_all(attrs={'tabindex': '-1'})
        if len(tabindex_negative) > 10:  # Arbitrary threshold
            issues.append("Excessive use of tabindex=-1 may cause focus issues")
        
        if issues:
            return False, "; ".join(issues)
        return True, "No obvious keyboard traps detected"
    
    def check_pointer_cancellation(self) -> Tuple[bool, str]:
        """Check for pointer cancellation patterns"""
        # Look for drag and drop implementations
        draggable = self.soup.find_all(attrs={'draggable': 'true'})
        
        if draggable and not self.soup.find(text=re.compile(r'undo|cancel|reset', re.I)):
            return False, "Draggable elements without undo mechanism"
        
        # Check for mousedown events (should use click instead)
        mousedown_elements = self.soup.find_all(attrs={'onmousedown': True})
        if mousedown_elements:
            return False, f"Found {len(mousedown_elements)} elements using mousedown (prefer click events)"
        
        return True, "No pointer cancellation issues detected"
    
    def check_label_in_name(self) -> Tuple[bool, str]:
        """Check if visible labels match accessible names"""
        issues = []
        
        inputs = self.soup.find_all(['input', 'button', 'select', 'textarea'])
        
        for inp in inputs[:10]:  # Check first 10 to avoid performance issues
            visible_label = self._find_label_for_input(inp)
            aria_label = inp.get('aria-label', '')
            placeholder = inp.get('placeholder', '')
            
            if visible_label and aria_label:
                label_text = visible_label.get_text().strip().lower()
                if label_text and label_text not in aria_label.lower():
                    issues.append(f"Mismatch between visible and accessible label")
                    break
        
        if issues:
            return False, "; ".join(issues)
        return True, "Labels match accessible names"
    
    def check_timing_adjustable(self) -> Tuple[bool, str]:
        """Check for timing mechanisms"""
        # Look for meta refresh
        meta_refresh = self.soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            if content and not content.startswith('0;'):
                return False, "Auto-refresh detected without user control"
        
        # Look for timeout-related text
        text = self.soup.get_text().lower()
        if 'session timeout' in text or 'time limit' in text:
            if 'extend' not in text and 'adjust' not in text:
                return False, "Timing limits mentioned without adjustment options"
        
        return True, "No problematic timing mechanisms detected"
    
    def check_seizures(self) -> Tuple[bool, str]:
        """Check for flashing content"""
        # Check for CSS animations that might flash
        style_tags = self.soup.find_all('style')
        
        for style in style_tags:
            content = style.string or ''
            if 'animation' in content.lower() and any(word in content.lower() for word in ['blink', 'flash', 'strobe']):
                return False, "Potential flashing animation detected in CSS"
        
        # Check for elements with animation classes
        animated = self.soup.find_all(class_=re.compile(r'flash|blink|strobe', re.I))
        if animated:
            return False, f"Found {len(animated)} elements with flashing-related classes"
        
        return True, "No flashing content detected"
    
    def check_bypass_blocks(self) -> Tuple[bool, str]:
        """Check for skip links"""
        # Look for skip links (usually at the top)
        skip_links = self.soup.find_all('a', href=re.compile(r'^#(main|content|skip)'))
        
        if not skip_links:
            return False, "No skip links found for bypassing repetitive content"
        
        # Check if skip link is one of the first elements
        body_children = list(self.soup.body.children) if self.soup.body else []
        first_elements = [elem for elem in body_children[:5] if hasattr(elem, 'name')]
        
        has_early_skip = any(
            skip_link in elem.find_all('a') if hasattr(elem, 'find_all') else False
            for elem in first_elements
            for skip_link in skip_links
        )
        
        if not has_early_skip:
            return False, "Skip link exists but not positioned early in document"
        
        return True, "Skip links properly implemented"
    
    def _find_label_for_input(self, input_elem):
        """Helper to find label for an input element"""
        input_id = input_elem.get('id')
        if input_id:
            label = self.soup.find('label', attrs={'for': input_id})
            if label:
                return label
        
        # Check if input is inside a label
        parent = input_elem.parent
        if parent and parent.name == 'label':
            return parent
        
        return None
    
    def run_all_checks(self) -> List[Dict]:
        """Run all compliance checks"""
        checks = [
            ("Meaningful Sequence", self.check_meaningful_sequence),
            ("Sensory Characteristics", self.check_sensory_characteristics),
            ("Use of Colour", self.check_use_of_colour),
            ("Keyboard Accessible", self.check_keyboard_accessible),
            ("No Keyboard Trap", self.check_no_keyboard_trap),
            ("Pointer Cancellation", self.check_pointer_cancellation),
            ("Label in Name", self.check_label_in_name),
            ("Timing Adjustable", self.check_timing_adjustable),
            ("Seizures", self.check_seizures),
            ("Bypass Blocks", self.check_bypass_blocks),
        ]
        
        results = []
        for check_name, check_func in checks:
            try:
                passed, details = check_func()
                results.append({
                    "check": check_name,
                    "status": "pass" if passed else "fail",
                    "details": details
                })
            except Exception as e:
                results.append({
                    "check": check_name,
                    "status": "error",
                    "details": f"Error running check: {str(e)}"
                })
        
        return results