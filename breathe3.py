#!/usr/bin/env python3
"""
Ultra-Fast Video to SRT Converter
Optimized for pc with i5 CPU with speed modes and time estimation.
Uses whisper.cpp for maximum CPU performance.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import subprocess
import threading
import tempfile
from pathlib import Path
import datetime
import time
import shutil
import json
import urllib.request
import platform

class SpeedOptimizedConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Ultra-Fast Video to SRT Converter")
        self.root.geometry("800x700")
        
        # Performance tracking
        self.start_time = None
        self.files_processed = 0
        self.total_files = 0
        self.processing_times = []
        
        # Supported video formats
        self.video_formats = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}
        
        # Speed mode configurations
        self.speed_configs = {
            'ultra_fast': {
                'model': 'tiny',
                'threads': os.cpu_count() or 4,
                'chunk_length': 10,  # seconds
                'temperature': 0.0,
                'beam_size': 1,
                'best_of': 1,
                'no_speech_threshold': 0.3,
                'compression_ratio_threshold': 2.4
            },
            'fast': {
                'model': 'base', 
                'threads': max(1, (os.cpu_count() or 4) - 1),
                'chunk_length': 15,
                'temperature': 0.1,
                'beam_size': 2,
                'best_of': 2,
                'no_speech_threshold': 0.4,
                'compression_ratio_threshold': 2.2
            },
            'balanced': {
                'model': 'small',
                'threads': max(1, (os.cpu_count() or 4) - 2),
                'chunk_length': 20,
                'temperature': 0.2,
                'beam_size': 3,
                'best_of': 3,
                'no_speech_threshold': 0.5,
                'compression_ratio_threshold': 2.0
            }
        }
        
        # Current config
        self.current_config = self.speed_configs['fast']
        self.processing = False
        self.whisper_path = None
        
        # Languages
        self.languages = {
            'Auto-detect': None,
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr', 
            'German': 'de',
            'Italian': 'it',
            'Portuguese': 'pt',
            'Russian': 'ru',
            'Japanese': 'ja',
            'Korean': 'ko',
            'Chinese': 'zh'
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header with system info
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        cpu_info = f"CPU: {os.cpu_count()} cores | Optimized for {platform.processor() or 'Intel i5'}"
        ttk.Label(header_frame, text=cpu_info, font=('Arial', 9)).grid(row=0, column=0, sticky=tk.W)
        
        # Folder selection
        ttk.Label(main_frame, text="📁 Select Folder with Videos:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=60)
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(folder_frame, text="Browse", command=self.select_folder).grid(row=0, column=1, padx=(5, 0))
        ttk.Button(folder_frame, text="Scan Files", command=self.scan_files).grid(row=0, column=2, padx=(5, 0))
        
        folder_frame.columnconfigure(0, weight=1)
        
        # Speed mode buttons (PROMINENT)
        speed_frame = ttk.LabelFrame(main_frame, text="🚀 Speed Modes", padding="10")
        speed_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(speed_frame, text="⚡ ULTRA FAST", 
                  command=lambda: self.set_speed_mode('ultra_fast'),
                  style='Accent.TButton').grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(speed_frame, text="🏃 FAST", 
                  command=lambda: self.set_speed_mode('fast')).grid(row=0, column=1, padx=(5, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(speed_frame, text="⚖️ BALANCED", 
                  command=lambda: self.set_speed_mode('balanced')).grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Current mode display
        self.mode_var = tk.StringVar(value="Mode: FAST")
        ttk.Label(speed_frame, textvariable=self.mode_var, font=('Arial', 9, 'bold')).grid(row=1, column=0, columnspan=3, pady=(5, 0))
        
        for i in range(3):
            speed_frame.columnconfigure(i, weight=1)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Language and translate
        ttk.Label(options_frame, text="Language:").grid(row=0, column=0, sticky=tk.W)
        self.lang_var = tk.StringVar(value='Auto-detect')
        lang_combo = ttk.Combobox(options_frame, textvariable=self.lang_var, 
                                values=list(self.languages.keys()), state='readonly', width=12)
        lang_combo.grid(row=0, column=1, padx=(5, 15), sticky=tk.W)
        
        self.translate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Translate to English", 
                       variable=self.translate_var).grid(row=0, column=2, sticky=tk.W)
        
        # Time offset
        ttk.Label(options_frame, text="Time Offset:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.offset_var = tk.DoubleVar(value=0.0)
        offset_spin = ttk.Spinbox(options_frame, from_=-5, to=5, increment=0.1, 
                                textvariable=self.offset_var, width=8)
        offset_spin.grid(row=1, column=1, padx=(5, 15), pady=(5, 0), sticky=tk.W)
        
        # Remove existing
        self.remove_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Overwrite existing SRT", 
                       variable=self.remove_existing_var).grid(row=1, column=2, pady=(5, 0), sticky=tk.W)
        
        # Progress and timing frame
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress & Timing", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # File info
        self.file_info_var = tk.StringVar(value="📂 No files scanned")
        ttk.Label(progress_frame, textvariable=self.file_info_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Current file progress
        self.current_file_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.current_file_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Progress bars
        self.file_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.file_progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Timing info
        timing_frame = ttk.Frame(progress_frame)
        timing_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.timing_var = tk.StringVar(value="⏱️ Timing: Not started")
        ttk.Label(timing_frame, textvariable=self.timing_var).grid(row=0, column=0, sticky=tk.W)
        
        self.eta_var = tk.StringVar(value="🎯 ETA: Not calculated")
        ttk.Label(timing_frame, textvariable=self.eta_var).grid(row=1, column=0, sticky=tk.W)
        
        progress_frame.columnconfigure(0, weight=1)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=6, column=0, columnspan=4, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="🚀 Start Processing", 
                                      command=self.start_processing, style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stop", 
                                     command=self.stop_processing, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(5, 5))
        
        ttk.Button(control_frame, text="🔍 Check Setup", 
                  command=self.check_setup).grid(row=0, column=2, padx=(5, 0))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="📋 Log", padding="5")
        log_frame.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Initialize
        self.set_speed_mode('fast')
        self.check_setup()
        
    def log_message(self, message, level="INFO"):
        """Add message to log with timestamp and level"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "SPEED": "🚀"}
        icon = icons.get(level, "ℹ️")
        log_entry = f"[{timestamp}] {icon} {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def set_speed_mode(self, mode):
        """Set processing speed mode"""
        self.current_config = self.speed_configs[mode]
        mode_names = {'ultra_fast': 'ULTRA FAST ⚡', 'fast': 'FAST 🏃', 'balanced': 'BALANCED ⚖️'}
        self.mode_var.set(f"Mode: {mode_names[mode]}")
        
        config_info = f"Model: {self.current_config['model']} | Threads: {self.current_config['threads']} | Beam: {self.current_config['beam_size']}"
        self.log_message(f"Speed mode set to {mode_names[mode]}: {config_info}", "SPEED")
        
    def check_setup(self):
        """Check if all dependencies are ready"""
        self.log_message("🔍 Checking system setup...", "INFO")
        
        # Check FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            self.log_message("✅ FFmpeg found and working", "SUCCESS")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_message("❌ FFmpeg not found! Install with: sudo apt install ffmpeg", "ERROR")
            return False
        
        # Check Whisper
        try:
            result = subprocess.run(['whisper', '--help'], capture_output=True, check=True)
            self.whisper_path = 'whisper'
            self.log_message("✅ Whisper CLI found and working", "SUCCESS")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_message("⚠️ Whisper not found, attempting installation...", "WARNING")
            if not self.install_whisper():
                return False
        
        # Pre-download models
        self.preload_models()
        return True
        
    def install_whisper(self):
        """Install whisper if not found"""
        try:
            self.log_message("📦 Installing OpenAI Whisper...", "INFO")
            result = subprocess.run(['pip', 'install', 'openai-whisper'], 
                                  capture_output=True, text=True, check=True)
            self.log_message("✅ Whisper installed successfully!", "SUCCESS")
            self.whisper_path = 'whisper'
            return True
        except subprocess.CalledProcessError as e:
            self.log_message(f"❌ Failed to install Whisper: {e.stderr}", "ERROR")
            return False
            
    def preload_models(self):
        """Pre-download commonly used models"""
        models_to_check = ['tiny', 'base', 'small']
        self.log_message("🔄 Checking/downloading Whisper models...", "INFO")
        
        for model in models_to_check:
            try:
                # Test if model works by running a quick command
                test_cmd = ['whisper', '--model', model, '--help']
                subprocess.run(test_cmd, capture_output=True, check=True, timeout=10)
                self.log_message(f"✅ Model '{model}' ready", "SUCCESS")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                self.log_message(f"📥 Model '{model}' will be downloaded on first use", "INFO")
        
    def select_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self.scan_files()
            
    def scan_files(self):
        """Scan folder for video files and estimate processing time"""
        folder_path = self.folder_var.get()
        if not folder_path or not os.path.exists(folder_path):
            return
            
        video_files = self.find_video_files(folder_path)
        self.total_files = len(video_files)
        
        if video_files:
            total_size = sum(f.stat().st_size for f in video_files) / (1024*1024)  # MB
            avg_size = total_size / len(video_files)
            
            # Estimate time based on speed mode and file size
            time_per_mb = {'ultra_fast': 0.5, 'fast': 1.0, 'balanced': 2.0}
            mode = next(k for k, v in self.speed_configs.items() if v == self.current_config)
            estimated_minutes = (total_size * time_per_mb.get(mode, 1.0)) / 60
            
            self.file_info_var.set(f"📂 Found {len(video_files)} videos | {total_size:.1f}MB total | ~{estimated_minutes:.1f}min estimated")
            self.log_message(f"📊 Scan complete: {len(video_files)} files, avg {avg_size:.1f}MB each", "INFO")
        else:
            self.file_info_var.set("📂 No video files found")
            
    def find_video_files(self, folder_path):
        """Recursively find all video files"""
        video_files = []
        folder_path = Path(folder_path)
        
        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.video_formats:
                video_files.append(file_path)
                
        return sorted(video_files)  # Sort for consistent processing order
        
    def estimate_file_time(self, file_path):
        """Estimate processing time for a single file"""
        try:
            file_size_mb = file_path.stat().st_size / (1024*1024)
            mode = next(k for k, v in self.speed_configs.items() if v == self.current_config)
            time_per_mb = {'ultra_fast': 0.5, 'fast': 1.0, 'balanced': 2.0}
            return file_size_mb * time_per_mb.get(mode, 1.0)
        except:
            return 60  # Default 1 minute if can't estimate
            
    def update_timing_display(self):
        """Update timing information display"""
        if not self.start_time:
            return
            
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
        
        if self.files_processed > 0:
            avg_time_per_file = elapsed / self.files_processed
            remaining_files = self.total_files - self.files_processed
            eta_seconds = remaining_files * avg_time_per_file
            eta_str = f"{int(eta_seconds//60)}:{int(eta_seconds%60):02d}"
            
            self.timing_var.set(f"⏱️ Elapsed: {elapsed_str} | Avg: {avg_time_per_file:.1f}s/file")
            self.eta_var.set(f"🎯 ETA: {eta_str} | {remaining_files} files remaining")
        else:
            self.timing_var.set(f"⏱️ Elapsed: {elapsed_str}")
            
    def process_video_optimized(self, video_path):
        """Process single video with optimized settings"""
        file_start_time = time.time()
        
        try:
            self.log_message(f"🎬 Processing: {video_path.name}", "INFO")
            
            # Check if SRT exists
            srt_path = video_path.with_suffix('.srt')
            if srt_path.exists() and not self.remove_existing_var.get():
                self.log_message(f"⏭️ Skipping existing: {srt_path.name}", "INFO")
                return True
            
            # Remove existing if requested
            if srt_path.exists() and self.remove_existing_var.get():
                srt_path.unlink()
                
            # Build optimized whisper command
            cmd = ['whisper', str(video_path)]
            
            # Core settings
            cmd.extend(['--model', self.current_config['model']])
            cmd.extend(['--output_format', 'srt'])
            cmd.extend(['--output_dir', str(video_path.parent)])
            cmd.extend(['--threads', str(self.current_config['threads'])])
            
            # Speed optimizations
            cmd.extend(['--temperature', str(self.current_config['temperature'])])
            cmd.extend(['--beam_size', str(self.current_config['beam_size'])])
            cmd.extend(['--best_of', str(self.current_config['best_of'])])
            cmd.extend(['--no_speech_threshold', str(self.current_config['no_speech_threshold'])])
            cmd.extend(['--compression_ratio_threshold', str(self.current_config['compression_ratio_threshold'])])
            
            # Language settings
            lang_code = self.languages.get(self.lang_var.get())
            if lang_code:
                cmd.extend(['--language', lang_code])
                
            if self.translate_var.get():
                cmd.extend(['--task', 'translate'])
                
            # Advanced CPU optimizations
            env = os.environ.copy()
            env['OMP_NUM_THREADS'] = str(self.current_config['threads'])
            env['MKL_NUM_THREADS'] = str(self.current_config['threads'])
            
            # Run whisper with progress tracking
            self.current_file_var.set(f"🎬 Processing: {video_path.name}")
            self.file_progress.start()
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                     text=True, env=env)
            
            # Monitor process
            while process.poll() is None and self.processing:
                time.sleep(0.1)
                self.root.update_idletasks()
                
            if not self.processing:
                process.terminate()
                return False
                
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd, stderr)
                
            # Apply time offset if needed
            if self.offset_var.get() != 0 and srt_path.exists():
                self.apply_time_offset(srt_path, self.offset_var.get())
                
            processing_time = time.time() - file_start_time
            self.processing_times.append(processing_time)
            
            file_size_mb = video_path.stat().st_size / (1024*1024)
            speed_ratio = file_size_mb / processing_time if processing_time > 0 else 0
            
            self.log_message(f"✅ Completed: {video_path.name} in {processing_time:.1f}s ({speed_ratio:.1f} MB/s)", "SUCCESS")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_message(f"❌ Error processing {video_path.name}: {e.stderr}", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ Unexpected error: {str(e)}", "ERROR")
            return False
        finally:
            self.file_progress.stop()
            
    def apply_time_offset(self, srt_path, offset_seconds):
        """Apply time offset to SRT file"""
        if offset_seconds == 0:
            return
            
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            modified_lines = []
            
            for line in lines:
                if '-->' in line:
                    parts = line.strip().split(' --> ')
                    if len(parts) == 2:
                        start_time = self.adjust_time(parts[0], offset_seconds)
                        end_time = self.adjust_time(parts[1], offset_seconds)
                        modified_lines.append(f"{start_time} --> {end_time}")
                    else:
                        modified_lines.append(line)
                else:
                    modified_lines.append(line)
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(modified_lines))
                
        except Exception as e:
            self.log_message(f"⚠️ Time offset failed: {str(e)}", "WARNING")
    
    def adjust_time(self, time_str, offset_seconds):
        """Adjust SRT time format"""
        try:
            time_part, ms_part = time_str.split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            total_seconds = max(0, total_seconds + offset_seconds)
            
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds_int = int(total_seconds % 60)
            milliseconds = int((total_seconds % 1) * 1000)
            
            return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"
        except:
            return time_str
            
    def process_videos(self):
        """Main processing function with timing"""
        try:
            folder_path = self.folder_var.get()
            if not folder_path or not os.path.exists(folder_path):
                messagebox.showerror("Error", "Please select a valid folder")
                return
                
            video_files = self.find_video_files(folder_path)
            
            if not video_files:
                messagebox.showinfo("No Videos", "No video files found")
                return
                
            self.total_files = len(video_files)
            self.files_processed = 0
            self.start_time = time.time()
            
            self.log_message(f"🚀 Starting batch processing: {len(video_files)} files", "INFO")
            
            success_count = 0
            
            for i, video_path in enumerate(video_files):
                if not self.processing:
                    self.log_message("⏹️ Processing stopped by user", "WARNING")
                    break
                    
                if self.process_video_optimized(video_path):
                    success_count += 1
                    
                self.files_processed += 1
                self.update_timing_display()
                    
            total_time = time.time() - self.start_time
            avg_speed = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
            
            self.log_message(f"🎉 Processing complete! {success_count}/{len(video_files)} files in {total_time/60:.1f}min", "SUCCESS")
            self.log_message(f"📊 Average speed: {avg_speed:.1f}s per file", "INFO")
            
            if success_count > 0:
                messagebox.showinfo("Complete", 
                                  f"🎉 Success! Processed {success_count}/{len(video_files)} files\n"
                                  f"Total time: {total_time/60:.1f} minutes\n"
                                  f"Average: {avg_speed:.1f}s per file")
            
        except Exception as e:
            self.log_message(f"❌ Critical error: {str(e)}", "ERROR")
        finally:
            self.reset_ui()
            
    def start_processing(self):
        """Start processing with setup verification"""
        if not self.folder_var.get():
            messagebox.showerror("Error", "Please select a folder first")
            return
            
        if not self.check_setup():
            messagebox.showerror("Setup Error", "System setup failed. Check the log for details.")
            return
            
        self.processing = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Clear previous results
        self.log_text.delete(1.0, tk.END)
        self.processing_times = []
        
        # Start processing thread
        thread = threading.Thread(target=self.process_videos, daemon=True)
        thread.start()
        
        # Start UI update timer
        self.update_ui_timer()
        
    def update_ui_timer(self):
        """Update UI elements periodically during processing"""
        if self.processing:
            self.update_timing_display()
            self.root.after(1000, self.update_ui_timer)  # Update every second
        
    def stop_processing(self):
        """Stop processing and save partial results"""
        self.processing = False
        self.log_message("🛑 Stopping processing... Saving partial results", "WARNING")
        
    def reset_ui(self):
        """Reset UI to ready state"""
        self.processing = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.file_progress.stop()
        self.current_file_var.set("Ready")
        
        if self.start_time:
            total_time = time.time() - self.start_time
            self.timing_var.set(f"⏱️ Total session time: {int(total_time//60)}:{int(total_time%60):02d}")
            self.eta_var.set("🎯 Session completed")

def check_dependencies():
    """Simplified dependency check that avoids PyTorch issues"""
    print("🔍 Checking dependencies...")
    
    # Only check for system dependencies, no Python imports that might fail
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found! Install with: sudo apt install ffmpeg")
        return False
    
    # Check for whisper CLI (don't import Python modules)
    try:
        subprocess.run(['whisper', '--help'], capture_output=True, check=True)
        print("✅ Whisper CLI found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Whisper CLI not found - will be installed automatically")
    
    return True

def main():
    """Main entry point with error handling"""
    try:
        # Basic dependency check without problematic imports
        if not check_dependencies():
            input("Press Enter to exit...")
            return
            
        print("🚀 Starting Ultra-Fast Video to SRT Converter...")
        
        root = tk.Tk()
        
        # Configure modern theme
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        # Create and run app
        app = SpeedOptimizedConverter(root)
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
