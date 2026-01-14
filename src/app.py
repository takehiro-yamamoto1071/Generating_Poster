import streamlit as st
import os
from generate import PosterGenerator
from io import BytesIO

# Set page layout
st.set_page_config(layout="wide", page_title="Poster Generator")

st.title("Poster Generator UI")

# --- Sidebar: Configuration ---
st.sidebar.header("1. Texts")
texts = {}
texts['title_en'] = st.sidebar.text_input("Lab Name (EN)", "RYOICHI SHINKUMA Lab.")
texts['subtitle_en'] = st.sidebar.text_input("Subtitle (EN)", "Design of Social information Network Systems")
texts['title_jp'] = st.sidebar.text_input("Main Title (JP)", "新熊研究室 見学会 & 交流会")
texts['target_audience'] = st.sidebar.text_input("Target Audience", "新2年生向け")
texts['date'] = st.sidebar.text_input("Date", "3/30(月)")
texts['welcome_msg'] = st.sidebar.text_input("Welcome Msg", "見学会だけ交流会だけの参加も大歓迎!")
texts['location_line1'] = st.sidebar.text_input("Location 1", "芝浦工業大学 豊洲キャンパス")
texts['location_line2'] = st.sidebar.text_input("Location 2", "研究棟 14F 14Q32")
texts['contact'] = st.sidebar.text_input("Contact", "Contact : a122063@shibaura-it.ac.jp 山本")

st.sidebar.header("2. Font Settings (Size & Spacing)")

# --- Font Selector ---
import glob
def get_system_fonts():
    # Simple scanner for Mac/Linux common paths
    paths = [
        "/System/Library/Fonts/*.ttc",
        "/System/Library/Fonts/*.ttf",
        "/Library/Fonts/*.ttc",
        "/Library/Fonts/*.ttf",
        "/Users/*/Library/Fonts/*.ttf", # User fonts
        "/Users/*/Library/Fonts/*.otf"
    ]
    fonts = []
    for p in paths:
        fonts.extend(glob.glob(os.path.expanduser(p)))
    
    # Filter for interesting ones or just return all
    # Let's map filename -> path for dropdown
    font_map = {os.path.basename(f): f for f in fonts}
    return font_map

system_fonts = get_system_fonts()
# Default to Hiragino if available
default_font_index = 0
keys = list(system_fonts.keys())
for i, k in enumerate(keys):
    if "Hiragino" in k:
        default_font_index = i
        break

selected_font_name = st.sidebar.selectbox("Select Font Family", keys, index=default_font_index)
selected_font_path = system_fonts.get(selected_font_name)

font_sizes = {}
spacings = {}

# Define text keys for iteration
text_keys = [
    ('title_en', "Title EN", 100),
    ('subtitle_en', "Subtitle EN", 60),
    ('title_jp', "Main Title JP", 140),
    ('target_audience', "Target Audience", 60), # Fixed key name
    ('date', "Date", 180),
    ('welcome_msg', "Welcome Msg", 70),
    ('info_large', "Location Large", 90),
    ('contact', "Contact Info", 40)
]

with st.sidebar.expander("Adjust Standard Texts"):
    for key, label, def_size in text_keys:
        c1, c2 = st.columns(2)
        font_sizes[key] = c1.number_input(f"Size: {label}", value=def_size, step=5, key=f"sz_{key}")
        spacings[key] = c2.number_input(f"Space: {label}", value=0, step=1, key=f"sp_{key}")

st.sidebar.header("3. Custom Texts")
if 'custom_blocks' not in st.session_state:
    st.session_state.custom_blocks = []

def add_block():
    st.session_state.custom_blocks.append({
        'text': "New Text", 'x': 500, 'y': 1000, 'size': 50, 'spacing': 0, 'color': '#000000'
    })

if st.sidebar.button("Add Custom Text Block"):
    add_block()

custom_texts_config = []
for i, block in enumerate(st.session_state.custom_blocks):
    with st.sidebar.expander(f"Block {i+1}", expanded=True):
        block['text'] = st.text_input("Text", block['text'], key=f"ct_txt_{i}")
        c1, c2 = st.columns(2)
        block['x'] = c1.number_input("X", value=block['x'], step=10, key=f"ct_x_{i}")
        block['y'] = c2.number_input("Y", value=block['y'], step=10, key=f"ct_y_{i}")
        
        c3, c4 = st.columns(2)
        block['size'] = c3.number_input("Size", value=block['size'], step=5, key=f"ct_sz_{i}")
        block['spacing'] = c4.number_input("Spacing", value=block['spacing'], step=1, key=f"ct_sp_{i}")
        
        block['color'] = st.color_picker("Color", block['color'], key=f"ct_col_{i}")
        
        # Button to remove? 
        # Streamlit state management for removal is tricky in a loop. 
        # Let's skip removal for now or add a clear all button.
        
    custom_texts_config.append(block)

st.sidebar.header("4. Custom Images")
if 'custom_image_blocks' not in st.session_state:
    st.session_state.custom_image_blocks = []

def add_image_block():
    st.session_state.custom_image_blocks.append({
        'x': 500, 'y': 500, 'w': 300, 'h': 200, 'scale': 1.0
    })

if st.sidebar.button("Add Custom Image Block"):
    add_image_block()

custom_images_config = []
for i, block in enumerate(st.session_state.custom_image_blocks):
    with st.sidebar.expander(f"Image Block {i+1}", expanded=True):
        f = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg'], key=f"ci_file_{i}")
        if f:
             block['image'] = f
        
        c1, c2 = st.columns(2)
        block['x'] = c1.number_input("X", value=block['x'], step=10, key=f"ci_x_{i}")
        block['y'] = c2.number_input("Y", value=block['y'], step=10, key=f"ci_y_{i}")
        
        c3, c4 = st.columns(2)
        block['w'] = c3.number_input("Width", value=block['w'], step=10, key=f"ci_w_{i}")
        block['h'] = c4.number_input("Height", value=block['h'], step=10, key=f"ci_h_{i}")
        
        block['scale'] = st.slider("Scale", 0.1, 3.0, block['scale'], 0.1, key=f"ci_s_{i}")
        
        # Only add to config if image is present (or we handle missing safely)
        if f:
            custom_images_config.append(block)

st.sidebar.header("5. QR Code")
qr_url = st.sidebar.text_input("QR URL", "https://forms.gle/VjpD3PCtuzxPBawz7")

# --- Layout Configuration ---
st.write("### Image Layout & Uploads")
col1, col2 = st.columns([1, 1])

# Image Slots Definition
slots = [
    "center_oval",
    "top_left", "top_right",
    "bottom_left", "bottom_right"
]

images = {}
layout_overrides = {}

# Default layout values for reference (matching generate.py)
defaults = {
    'top_left': {'x': 50, 'y': 750, 'w': 900, 'h': 650},
    'top_right': {'x': 1050, 'y': 750, 'w': 900, 'h': 650},
    'bottom_left': {'x': 50, 'y': 1420, 'w': 900, 'h': 650},
    'bottom_right': {'x': 1050, 'y': 1420, 'w': 900, 'h': 650},
    'center_oval': {'x': 500, 'y': 1110, 'w': 1000, 'h': 600}
}

for i, slot in enumerate(slots):
    # Determine column (Left or Right)
    c = col1 if i < 3 else col2
    
    with c.expander(f"Slot: {slot}", expanded=i==0):
        # File Uploader
        uploaded_file = st.file_uploader(f"Upload Image for {slot}", type=['png', 'jpg', 'jpeg'], key=f"file_{slot}")
        if uploaded_file:
            images[slot] = uploaded_file
        
        # Layout Inputs
        st.caption("Fine-tune Position & Size")
        def_v = defaults.get(slot, {'x':0, 'y':0, 'w':100, 'h':100})
        
        # Scale slider
        scale = st.slider(f"Scale (Zoom) {slot}", 0.1, 3.0, 1.0, 0.1, key=f"s_{slot}")

        l_c1, l_c2, l_c3, l_c4 = st.columns(4)
        x = l_c1.number_input(f"X", value=def_v['x'], step=10, key=f"x_{slot}")
        y = l_c2.number_input(f"Y", value=def_v['y'], step=10, key=f"y_{slot}")
        w = l_c3.number_input(f"W", value=def_v['w'], step=10, key=f"w_{slot}")
        h = l_c4.number_input(f"H", value=def_v['h'], step=10, key=f"h_{slot}")
        
        layout_overrides[slot] = {"x": int(x), "y": int(y), "w": int(w), "h": int(h), "scale": scale}

# --- Generation Logic ---

@st.cache_resource
def get_generator_class():
    """Cache the class definition/font loading if possible, 
    but here we just return the class or instance wrapper if needed.
    """
    return PosterGenerator

def generate_preview(config):
    output_path = "generated_poster_ui.png"
    gen = PosterGenerator(output_path, config)
    gen.generate()
    return output_path

# Auto-generate if any input changes
# We wrap this in a container to keep UI stable
st.write("### Preview")

# Construction config dictionary from current state
config = {
    "texts": texts,
    "images": images,
    "layout": layout_overrides,
    "font_sizes": font_sizes,
    "spacings": spacings,
    "custom_texts": custom_texts_config,
    "custom_images": custom_images_config,
    "qr_url": qr_url,
    "font_path": selected_font_path
}

if images:
    try:
        # Generate immediately
        with st.spinner("Updating preview..."):
            preview_path = generate_preview(config)
            
        col_prev, col_dl = st.columns([3, 1])
        with col_prev:
            st.image(preview_path, caption="Live Preview", use_container_width=True)
        
        with col_dl:
            with open(preview_path, "rb") as file:
                st.download_button(
                    label="Download Poster (PNG)",
                    data=file,
                    file_name="poster.png",
                    mime="image/png"
                )
            
            # QR Download
            temp_gen = PosterGenerator("dummy", config)
            qr_img = temp_gen.get_qr_image()
            if qr_img:
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                st.download_button(
                    label="Download QR Only",
                    data=buf.getvalue(),
                    file_name="qr_code.png",
                    mime="image/png"
                )

    except Exception as e:
        st.error(f"Generation failed: {e}")
else:
    st.info("Upload at least one image to see the preview.")
