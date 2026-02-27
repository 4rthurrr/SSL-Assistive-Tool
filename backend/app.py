from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from nlp_grammar import get_ssl_sequence, get_ssl_display_sequence # Legacy Rule-based
# from inference_engine import LearnedInference
from concepts import get_sinhala_display
from video_manager import find_video_path
from moviepy.editor import VideoFileClip, concatenate_videoclips
import os
import uuid
import shutil
from avatar_engine import AvatarEngine
try:
    from skeleton_generator import SkeletonGenerator
    from ai_avatar_engine import NeuralAvatarEngine
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: AI Modules missing.")

from context_engine import process_input

app = Flask(__name__)
CORS(app)

# Output Directory
OUTPUT_DIR = "static/outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Avatar Assets Directory
AVATAR_DIR = "assets/avatars"
if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

# Init Learned Model
# print("⌛ Initializing Learned Inference Engine...")
# learned_engine = LearnedInference()
# print("✅ Inference Engine Ready.")

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '')
        style = data.get('style', 'normal') # 'normal', 'skeleton'
        source_image = data.get('source_image', 'source.png') # Default to source.png
        
        print(f"📨 Request: '{text}' (Style: {style}, Source: {source_image})")
        
        # 1. Context Awareness: Simplify/Translate input
        # This converts English "Mother" -> Sinhala "අම්මා"
        processed_text = process_input(text)
        print(f"🧠 Processed Text: '{processed_text}'")
        
        # 2. Get SSL Grammar (Fully Learned)
        ssl_words = get_ssl_sequence(processed_text) # Old Rule-based
        ssl_display_words = get_ssl_display_sequence(ssl_words)
        
        # ssl_words = learned_engine.translate(processed_text)
        # ssl_display_words = [get_sinhala_display(c) or c for c in ssl_words]
        print(f"🔤 SSL Sequence: {ssl_words}")
        print(f"🔤 SSL Display: {ssl_display_words}")
        
        generated_clips = []
        word_timings = []
        current_time = 0.0
        
        # 3. Find Videos for each word and calculate timings
        for i, word in enumerate(ssl_words):
            display_word = ssl_display_words[i] if i < len(ssl_display_words) else word
            video_path = find_video_path(word)
            
            if video_path:
                print(f"✅ Found video for '{word}': {video_path}")
                try:
                    clip = VideoFileClip(video_path)
                    generated_clips.append(clip)
                    
                    duration = clip.duration
                    word_timings.append({
                        "word": display_word,
                        "start": current_time,
                        "end": current_time + duration
                    })
                    current_time += duration
                    
                except Exception as e:
                    print(f"❌ Error loading video {video_path}: {e}")
                    # Still add the word but with 0 duration or handle gracefully
                    word_timings.append({
                        "word": display_word,
                        "start": current_time,
                        "end": current_time
                    })
            else:
                print(f"⚠️ Missing Video for: {word}")
                word_timings.append({
                    "word": display_word,
                    "start": current_time,
                    "end": current_time
                })


        if not generated_clips:
            return jsonify({
                "error": "No videos found", 
                "ssl_grammar": ssl_words,
                "ssl_grammar_display": ssl_display_words
            }), 404

        # 4. Concatenate Clips (Stitching)
        final_clip = concatenate_videoclips(generated_clips, method="compose")
        
        # Generate Filename
        filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        # Save Raw Video
        final_clip.write_videofile(output_path, codec="libx264", fps=24)
        final_clip.close() # <--- CRITICAL: Release file handle
        
        # 5. Handle AI Avatar Style
        if style == 'ai_real':
            print("🤖 Generating AI Real Avatar...")
            if not AI_AVAILABLE:
                print("❌ AI Available=False. Check imports.")
            else:
                try:
                    # A. Generate Driver
                    print("   [Step 1] Initializing SkeletonGenerator...")
                    sk_gen = SkeletonGenerator()
                    driver_path = os.path.join(OUTPUT_DIR, f"driver_{filename}")
                    
                    if not os.path.exists(output_path):
                         print("❌ Normal video failed, cannot generate Skeleton Driver.")
                    else:
                        print(f"   [Step 2] Creating Skeleton Driver from: {output_path}")
                        skeleton_path = sk_gen.create_skeleton_video([output_path], driver_path)
                        
                        if not skeleton_path:
                            print("❌ Skeleton Generation FAILED (Returned None).")
                        else:
                            print(f"💀 Driver Created (Synced): {skeleton_path}")
                            
                            # B. Run Neural Engine
                            print("   [Step 3] Initializing NeuralAvatarEngine...")
                            ai_engine = NeuralAvatarEngine("config/vox-256.yaml", "checkpoints/vox-cpk.pth.tar")
                            
                            # Source Image (Ignored by engine now, but path needed)
                            teacher_img = os.path.join("assets", "teacher.jpg")
                            
                            ai_filename = f"ai_{filename}"
                            ai_output_path = os.path.join(OUTPUT_DIR, ai_filename)
                            
                            print("   [Step 4] Running animate_avatar (Hologram Mode)...")
                            result_path = ai_engine.animate_avatar(teacher_img, skeleton_path, ai_output_path)
                            
                            if result_path and os.path.exists(result_path):
                                print(f"✅ AI Video Success: {result_path}")
                                video_url = f"http://localhost:5000/{OUTPUT_DIR}/{ai_filename}"
                                return jsonify({
                                    "video_url": video_url, 
                                    "ssl_grammar": ssl_words, 
                                    "ssl_grammar_display": ssl_display_words,
                                    "word_timings": word_timings,
                                    "mode": "ai_real"
                                })
                            else:
                                print(f"❌ AI Animation returned None/Fail. Result Path: {result_path}")
                except Exception as e:
                     import traceback
                     traceback.print_exc()
                     print(f"❌ AI Generation Crash: {e}")
        

        # 6. Handle Skeleton Style
        if style == 'skeleton':
            print("💀 Generating Skeleton Avatar Video...")
            sk_filename = f"sk_{filename}"
            sk_output_path = os.path.join(OUTPUT_DIR, sk_filename)
            
            from avatar_engine import generate_avatar_video
            success = generate_avatar_video(output_path, sk_output_path, style='skeleton')
            
            if success:
                print("✅ Skeleton Generation Successful!")
                video_url = f"http://localhost:5000/{OUTPUT_DIR}/{sk_filename}"
                return jsonify({
                    "video_url": video_url, 
                    "ssl_grammar": ssl_words, 
                    "ssl_grammar_display": ssl_display_words,
                    "word_timings": word_timings,
                    "mode": "skeleton"
                })
            else:
                print("❌ Skeleton Generation Failed. Falling back to normal video.")
        

        
        # Default Return (Normal Video)
        video_url = f"http://localhost:5000/{OUTPUT_DIR}/{filename}"
        return jsonify({
            "video_url": video_url, 
            "ssl_grammar": ssl_words, 
            "ssl_grammar_display": ssl_display_words,
            "word_timings": word_timings,
            "mode": "normal"
        })

    except Exception as e:
        print(f"❌ Server Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/avatars', methods=['GET'])
def list_avatars():
    """ List available avatar images """
    try:
        files = [f for f in os.listdir(AVATAR_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        # Include default source.png if it exists in root
        if os.path.exists('source.png'):
            files.insert(0, 'source.png')
        return jsonify({"avatars": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    """ Upload a new avatar image """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if file:
            filename = file.filename
            # Simple validation
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                 return jsonify({"error": "Invalid file type. Only PNG/JPG allowed."}), 400
                 
            save_path = os.path.join(AVATAR_DIR, filename)
            file.save(save_path)
            return jsonify({"message": "File uploaded successfully", "filename": filename})
            
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/static/outputs/<path:filename>')
def serve_video(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)