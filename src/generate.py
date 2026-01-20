from PIL import Image, ImageDraw, ImageFont, ImageOps
import qrcode
import os
import platform

class PosterGenerator:
    def __init__(self, output_path, config):
        self.output_path = output_path
        self.config = config
        self.width = 2000
        self.height = 2828
        self.bg_color = (255, 255, 255)
        self.footer_color = (34, 139, 34) # Forest Green approx
        self.text_orange = (200, 70, 0)
        self.text_black = (0, 0, 0)
        self.text_white = (255, 255, 255)
        
        self.poster = Image.new('RGB', (self.width, self.height), self.bg_color)
        self.draw = ImageDraw.Draw(self.poster)
        self.fonts = {}
        self._load_fonts()

    def _load_fonts(self):
        font_config = self.config.get('font_sizes', {})
        configured_font_path = self.config.get('font_path') # User selected font
        
        # Default sizes
        defaults = {
            'title_en': 100,
            'subtitle_en': 60,
            'title_jp': 140,
            'target': 60,
            'date': 180,
            'info_large': 90,
            'info_mid': 70,
            'contact': 40
        }
        
        # Determine font path
        font_path = "arial.ttf" # Fallback
        
        if configured_font_path and os.path.exists(configured_font_path):
             font_path = configured_font_path
        else:
            # System defaults logic
            system = platform.system()
            if system == "Darwin": # macOS
                potential_paths = [
                    "/System/Library/Fonts/Hiragino Sans GB.ttc",
                    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
                    "/System/Library/Fonts/Heiti SC.ttc"
                ]
                for p in potential_paths:
                    if os.path.exists(p):
                        font_path = p
                        break
            elif system == "Windows":
                font_path = "msgothic.ttc"
        
        try:
            for key, default_size in defaults.items():
                size = font_config.get(key, default_size)
                self.fonts[key] = ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"Font loading failed ({e}). Using default.")
            default = ImageFont.load_default()
            self.fonts = {k: default for k in defaults.keys()}

    def draw_layout(self):
        # Draw Green Footer
        footer_y = 2100
        self.draw.rectangle([(0, footer_y), (self.width, self.height)], fill=self.footer_color)

    def draw_text_spaced(self, xy, text, font, fill, anchor, spacing=0):
        """Draws text with custom letter spacing.
        Anchor handling is simplified:
        - 'mm': Center horizontally and vertically (approx)
        - 'la': Left Align (standard)
        - 'ma': Center Horizontal, Top Align (standard)
        
        Real anchor support for spaced text is complex. 
        We will calculate total width and adjust start_x.
        """
        if not text:
            return

        # Calculate total width
        total_width = 0
        char_widths = []
        for char in text:
            bbox = font.getbbox(char)
            # bbox is (left, top, right, bottom)
            w = bbox[2] - bbox[0]
            # Add some base advance if needed, but bbox width is usually close enough for PIL
            # Actually PIL's getlength is better
            w = font.getlength(char)
            char_widths.append(w)
            total_width += w
        
        total_width += spacing * (len(text) - 1)
        
        x, y = xy
        
        # Adjust Start X based on Anchor
        if 'm' in anchor[0]: # Center Horizontal
            start_x = x - total_width / 2
        elif 'l' in anchor[0]: # Left
            start_x = x
        elif 'r' in anchor[0]: # Right
            start_x = x - total_width
        else:
            start_x = x # Default to left
            
        # Adjust Start Y based on Anchor
        # Simplification: For 'mm', we assume y is center.
        # PIL default draw.text handles vertical alignment well, but we are drawing char by char.
        # We need to compute ascent/descent if we want perfect vertical centering.
        # For this usage, let's trust that passing the right y for a standard baseline or top works 
        # and we only manually adjust X.
        # BUT, if anchor is 'mm', Y was calculated as center. 
        # We should calculate font height to adjust Y if we draw char-by-char with top-left defaults?
        # Actually, draw.text((x,y), char, anchor='la') draws baseline or top depending on font?
        # Let's use anchor='mm' for each char? No, that centers each char.
        # Let's use 'la' (Left Ascender/Top) as base and shift our start_xy.
        
        # To match existing code which uses 'mm' or 'la':
        # If input anchor was 'mm', we must shift y up by half height.
        
        ascent, descent = font.getmetrics()
        font_height = ascent + descent
        
        draw_y = y
        if 'm' in anchor[1]: # Center Vertical
             # Shift up by half height (approx)
             draw_y = y - ascent / 2 - descent / 2 # varied logic depending on exact needs
             # Actually, simpler: Use font.getbbox(text) to find height?
             # Let's stick to simple:
             pass 

        # Drawing Loop
        # We will use the original anchor Y behavior by letting PIL handle Y.
        # We only manipulate X.
        # But wait, if we use separate draw.text calls, 'mm' won't work for the whole string.
        # Strategy:
        # Use 'ls' (Left Baseline) or 'la' (Left Ascender) for individual chars?
        # Let's use 'la'.
        
        current_x = start_x
        
        # Vertical adjustment for 'mm'
        if anchor == 'mm':
            # Calculate height of string
            bbox = font.getbbox(text)
            h = bbox[3] - bbox[1]
            draw_y = y - h / 2
            # Re-adjust visual Y? 
            # The previous 'mm' calls worked fine. Let's try to mimic that.
            # If I draw each char with 'la' at computed Y...
            pass
        elif anchor == 'mm':
             # fallback for safety if complex logic fails? 
             # No, let's implement X-spacing only and rely on 'la' or 'ma' -> converted to Left-based X.
             pass

        # Override Y logic:
        # If anchor implies vertical centering ('mm'), find top-left Y
        if 'm' in anchor[1]:
             # Get height
             _, _, _, h = font.getbbox(text) # approx
             draw_y = y - h/2
        else:
             draw_y = y

        for i, char in enumerate(text):
            self.draw.text((current_x, draw_y), char, font=font, fill=fill, anchor='la') # always draw from top-left of char
            current_x += char_widths[i] + spacing

    def draw_text(self):
        texts = self.config.get('texts', {})
        spacings = self.config.get('spacings', {}) # Dict of spacings
        
        # Helper to get spacing with default 0
        def get_spacing(key):
            return spacings.get(key, 0)

        # --- Header ---
        self.draw_text_spaced((self.width/2, 150), texts.get('title_en', ''), self.fonts['title_en'], self.text_black, "mm", get_spacing('title_en'))
        self.draw_text_spaced((self.width/2, 250), texts.get('subtitle_en', ''), self.fonts['subtitle_en'], self.text_black, "mm", get_spacing('subtitle_en'))
        
        self.draw_text_spaced((self.width/2, 450), texts.get('title_jp', ''), self.fonts['title_jp'], self.text_orange, "mm", get_spacing('title_jp'))
        self.draw_text_spaced((self.width/2, 600), texts.get('target_audience', ''), self.fonts['target'], self.text_black, "mm", get_spacing('target_audience'))

        # --- Footer ---
        footer_start_x = 100
        footer_y = 2150
        
        self.draw_text_spaced((footer_start_x, footer_y), texts.get('date', ''), self.fonts['date'], self.text_white, "la", get_spacing('date'))
        self.draw_text_spaced((footer_start_x, footer_y + 220), texts.get('welcome_msg', ''), self.fonts['info_mid'], self.text_white, "la", get_spacing('welcome_msg'))
        self.draw_text_spaced((footer_start_x, footer_y + 320), texts.get('location_line1', ''), self.fonts['info_large'], self.text_white, "la", get_spacing('location_line1'))
        self.draw_text_spaced((footer_start_x, footer_y + 430), texts.get('location_line2', ''), self.fonts['info_large'], self.text_white, "la", get_spacing('location_line2'))
        self.draw_text_spaced((footer_start_x, footer_y + 550), texts.get('contact', ''), self.fonts['contact'], self.text_white, "la", get_spacing('contact'))
        
        # --- Custom Texts ---
        custom_texts = self.config.get('custom_texts', [])
        for c in custom_texts:
            # c = {text, x, y, size, spacing, color, font_path}
            # Simplified: assume default font (arial/hiragino) but custom size
            # Load font on the fly or cache?
            # For simplicity, create font here.
            try:
                # Use same font logic as _load_fonts logic...
                # Ideally config passes absolute path or we reuse existing variable
                font_path = "arial.ttf" # basic fallback, should be robust
                # If we have self.fonts['title_en'] we could reuse its path info?
                # Let's try to get path from one of the loaded fonts if possible or re-detect.
                pass 
                
                size = c.get('size', 50)
                # Re-detect path quickly
                system = platform.system()
                if system == "Darwin" and os.path.exists("/System/Library/Fonts/Hiragino Sans GB.ttc"):
                     font_path = "/System/Library/Fonts/Hiragino Sans GB.ttc"
                
                font = ImageFont.truetype(font_path, size)
                
                # Draw
                color = c.get('color', (0,0,0))
                # Convert hex to rgb if needed? Streamlit color picker returns hex.
                # If string, PIL handles hex.
                
                self.draw_text_spaced(
                    (c['x'], c['y']), 
                    c['text'], 
                    font, 
                    color, 
                    "la", # Default to Left-Top align for custom texts
                    c.get('spacing', 0)
                )
            except Exception as e:
                print(f"Failed to draw custom text: {e}")

    def _process_image(self, image_input, target_size, is_oval=False, scale=1.0):
        """Loads, resizing (centering), scaling, and optionally masking an image."""
        if not image_input:
            return None
            
        try:
            # Support both file paths and file-like objects (e.g. BytesIO)
            if isinstance(image_input, str):
                if not os.path.exists(image_input):
                    return None
            
            img = Image.open(image_input).convert("RGBA")
            
            # 1. Base Fit: Resize to fully cover target_size (LANCZOS)
            # ImageOps.fit crops to exact aspect ratio of target_size
            # We want to allow zooming out, so maybe fit is too aggressive?
            # Actually, standard collage behavior is "cover", then zoom in/out.
            
            # Calculate base sizing to COVER the target area
            img_ratio = img.width / img.height
            target_ratio = target_size[0] / target_size[1]
            
            if img_ratio > target_ratio:
                 # Image is wider than target
                 base_height = target_size[1]
                 base_width = int(base_height * img_ratio)
            else:
                 # Image is taller than target
                 base_width = target_size[0]
                 base_height = int(base_width / img_ratio)
                 
            # Apply base resize
            img = img.resize((base_width, base_height), Image.Resampling.LANCZOS)
            
            # 2. Scale (Zoom)
            if scale != 1.0:
                new_w = int(base_width * scale)
                new_h = int(base_height * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 3. Center Crop to target_size
            # Create a transparent canvas of target_size
            canvas = Image.new('RGBA', target_size, (255, 255, 255, 0))
            
            # Paste scaled image centered
            # img coordinates
            paste_x = (target_size[0] - img.width) // 2
            paste_y = (target_size[1] - img.height) // 2
            
            canvas.paste(img, (paste_x, paste_y))
            img = canvas
            
            if is_oval:
                mask = Image.new('L', target_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, target_size[0], target_size[1]), fill=255)
                img.putalpha(mask)
                
            return img
        except Exception as e:
            print(f"Error processing image {image_input}: {e}")
            return None

    def embed_images(self):
        images = self.config.get('images', {})
        user_layout = self.config.get('layout', {})
        
        # Default Layout Configuration
        # Canvas Width: 2000
        # Grid Y-range: approx 750 - 2070
        layout = {
            'top_left': {'x': 50, 'y': 750, 'w': 900, 'h': 650},
            'top_right': {'x': 1050, 'y': 750, 'w': 900, 'h': 650},
            'bottom_left': {'x': 50, 'y': 1420, 'w': 900, 'h': 650},
            'bottom_right': {'x': 1050, 'y': 1420, 'w': 900, 'h': 650},
            'center_oval': {'x': 500, 'y': 1110, 'w': 1000, 'h': 600}
        }

        # Update with user overrides
        for key, val in user_layout.items():
            if key in layout:
                layout[key].update(val)
        
        # 1. Corner Images (Grid)
        corners = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
        for key in corners:
            if key in images:
                l = layout[key]
                scale = l.get('scale', 1.0)
                img = self._process_image(images[key], (l['w'], l['h']), scale=scale)
                if img:
                    self.poster.paste(img, (l['x'], l['y']), img)

        # 2. Center Oval (Top Layer)
        if 'center_oval' in images:
            l = layout['center_oval']
            scale = l.get('scale', 1.0)
            oval_img = self._process_image(images['center_oval'], (l['w'], l['h']), is_oval=True, scale=scale)
            if oval_img:
                self.poster.paste(oval_img, (l['x'], l['y']), oval_img)
                
        # 3. Custom Images
        custom_images = self.config.get('custom_images', [])
        for cdict in custom_images:
            # cdict = {'image': data/path, 'x':..., 'y':..., 'w':..., 'h':..., 'scale':...}
            img_input = cdict.get('image')
            if not img_input:
                continue
                
            w = cdict.get('w', 200)
            h = cdict.get('h', 200)
            x = cdict.get('x', 0)
            y = cdict.get('y', 0)
            scale = cdict.get('scale', 1.0)
            
            # Use existing process_image which handles resizing/scaling
            p_img = self._process_image(img_input, (w, h), is_oval=False, scale=scale)
            
            if p_img:
                self.poster.paste(p_img, (x, y), p_img)

    def get_qr_image(self):
        """Generates the QR code image."""
        qr_data = self.config.get('qr_url')
        if not qr_data:
            return None
            
        qr = qrcode.QRCode(box_size=12, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").convert("RGB")

    def embed_qr(self):
        qr_img = self.get_qr_image()
        if qr_img:
            label = "↑申し込みフォーム"
            qr_size = 400
            qr_img = qr_img.resize((qr_size, qr_size))
            
            x_pos = self.width - qr_size - 100
            y_pos = 2200
            
            self.poster.paste(qr_img, (x_pos, y_pos))
            self.draw.text((x_pos + qr_size/2, y_pos + qr_size + 20), label, fill=self.text_white, font=self.fonts['contact'], anchor="mt")

    def generate(self):
        print("Starting poster generation...")
        self.draw_layout()
        self.draw_text()
        self.embed_images()
        self.embed_qr()
        
        try:
            self.poster.save(self.output_path)
            print(f"Success! Poster saved to {self.output_path}")
        except Exception as e:
            print(f"Error saving poster: {e}")

# --- Configuration & Execution ---
if __name__ == "__main__":
    
    config = {
        "texts": {
            "title_en": "Lab.",
            "subtitle_en": "***",
            "title_jp": "交流会",
            "target_audience": "新2年生向け",
            "date": "3/30(月)",
            "welcome_msg": "見学会だけ交流会だけの参加も大歓迎!",
            "location_line1": "***大学",
            "location_line2": "**F ***教室", 
            "contact": "Contact : メールアドレス"
        },
        "images": {
            # Use the same image for all slots for demo
            "center_oval": "./resized_900x600_1.png",
            "top_left": "./resized_900x600_2.png",
            "top_right": "./resized_900x600_3.png",
            "bottom_left": "./resized_900x600_4.png",
            "bottom_right": "./resized_900x600_5.png"
        },
        # Optional: Fine-tune layout
        "layout": {
            "center_oval": {"y": 1150}, # Example: Move oval down slightly
            # "top_left": {"w": 800}    # Example: Make top-left smaller
        },
        "qr_url": "https://forms.gle/VjpD3PCtuzxPBawz7"
    }

    output_file = "generated_poster_collage.png"
    
    generator = PosterGenerator(output_file, config)
    generator.generate()
