import os
import re
import subprocess
import tempfile
from pathlib import Path
from pdf2zh import __version__

import gradio as gr
import numpy as np
import pymupdf

# Map service names to pdf2zh service options
service_map = {
    "Google": "google",
    "DeepL": "deepl",
    "DeepLX": "deeplx",
    "Ollama": "ollama",
    "OpenAI": "openai",
    "Azure": "azure",
}
lang_map = {
    "Chinese": "zh",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Korean": "ko",
    "Russian": "ru",
    "Spanish": "es",
    "Italian": "it",
}


def pdf_preview(file):
    doc = pymupdf.open(file)
    page = doc[0]
    pix = page.get_pixmap()
    image = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
    return image


def upload_file(file, service, progress=gr.Progress()):
    """Handle file upload, validation, and initial preview."""
    if not file or not os.path.exists(file):
        return None, None, gr.update(visible=False)

    progress(0.3, desc="Converting PDF for preview...")
    try:
        # Convert first page for preview
        preview_image = pdf_preview(file)

        return file, preview_image, gr.update(visible=True)
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return None, None, gr.update(visible=False)


def translate(
    file_path, service, model_id, lang, page_range, extra_args, hotwords, save_dir, openai_api_key, openai_base_url, thinking_level, progress=gr.Progress()
):
    """Translate PDF content using selected service."""
    if not file_path:
        return (
            None,
            None,
            gr.update(visible=False),
            gr.update(visible=False),
        )

    progress(0, desc="Starting translation...")

    # Create a temporary working directory using Gradio's file utilities
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create safe paths using pathlib
        temp_path = Path(temp_dir)
        input_pdf = temp_path / "input.pdf"

        # Copy input file to temp directory
        progress(0.2, desc="Preparing files...")
        with open(file_path, "rb") as src, open(input_pdf, "wb") as dst:
            dst.write(src.read())

        if hotwords and hotwords.strip():
            os.environ["PDF2ZH_HOTWORDS"] = hotwords.strip()
            try:
                with open("saved_hotwords.txt", "w", encoding="utf-8") as f:
                    f.write(hotwords.strip())
            except Exception:
                pass
            # Clear cache to force re-translation with new hotwords
            cache_dir = os.path.join(tempfile.gettempdir(), 'cache')
            if os.path.exists(cache_dir):
                import shutil
                shutil.rmtree(cache_dir, ignore_errors=True)
        else:
            if "PDF2ZH_HOTWORDS" in os.environ:
                del os.environ["PDF2ZH_HOTWORDS"]
            try:
                if os.path.exists("saved_hotwords.txt"):
                    os.remove("saved_hotwords.txt")
            except Exception:
                pass

        if service == "OpenAI":
            if openai_api_key and openai_api_key.strip():
                os.environ["OPENAI_API_KEY"] = openai_api_key.strip()
            if openai_base_url and openai_base_url.strip():
                os.environ["OPENAI_BASE_URL"] = openai_base_url.strip()
            os.environ["PDF2ZH_THINKING_LEVEL"] = thinking_level

        selected_service = service_map.get(service, "google")
        lang_to = lang_map.get(lang, "zh")

        # Execute translation in temp directory with real-time progress
        progress(0.3, desc=f"Starting translation with {selected_service}...")

        # Create output directory for translated files
        output_dir = Path(save_dir) if save_dir.strip() else Path(r"D:\报账\报账\报销明细\报销明细\YJJ-报销明细\venv")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_output = output_dir / f"translated_{os.path.basename(file_path)}"
        final_output_dual = output_dir / f"dual_{os.path.basename(file_path)}"

        # Prepare extra arguments
        extra_args = extra_args.strip()
        # Add page range arguments
        if page_range == "All":
            extra_args += ""
        elif page_range == "First":
            extra_args += " -p 1"
        elif page_range == "First 5 pages":
            extra_args += " -p 1-5"

        # Execute translation command
        if selected_service == "google":
            lang_to = "zh-CN" if lang_to == "zh" else lang_to

        if selected_service in ["ollama", "openai"]:
            command = f'cd /d "{temp_path}" && pdf2zh "{input_pdf}" -lo {lang_to} -s {selected_service}:{model_id} {extra_args}'
        else:
            command = f'cd /d "{temp_path}" && pdf2zh "{input_pdf}" -lo {lang_to} -s {selected_service} {extra_args}'
        print(f"Executing command: {command}")
        print(f"Files in temp directory: {os.listdir(temp_path)}")

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        # Monitor progress from command output
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(f"Command output: {output.strip()}")
                # Look for percentage in output
                match = re.search(r"(\d+)%", output.strip())
                if match:
                    percent = int(match.group(1))
                    # Map command progress (0-100%) to our progress range (30-80%)
                    progress_val = 0.3 + (percent * 0.5 / 100)
                    progress(progress_val, desc=f"Translating content: {percent}%")

        # Get the return code
        return_code = process.poll()
        print(f"Command completed with return code: {return_code}")

        # Check if translation was successful
        translated_file = temp_path / f"input-{lang_to}.pdf"
        if not translated_file.exists():
            translated_file = temp_path / "input-zh.pdf"
        
        print(f"Files after translation: {os.listdir(temp_path)}")

        if not translated_file.exists():
            print("Translation failed: No output files found")
            return (
                None,
                None,
                gr.update(visible=False),
                gr.update(visible=False),
            )

        # Copy the translated files to permanent locations
        progress(0.8, desc="Saving translated files...")

        saved_files = []
        if translated_file.exists():
            with open(translated_file, "rb") as src, open(final_output, "wb") as dst:
                dst.write(src.read())
            saved_files.append(str(final_output))

        dual_file = temp_path / "input-dual.pdf"
        if not dual_file.exists():
            dual_file = temp_path / f"input-{lang_to}-dual.pdf"
        if dual_file.exists():
            with open(dual_file, "rb") as src, open(final_output_dual, "wb") as dst:
                dst.write(src.read())
            saved_files.append(str(final_output_dual))

        # Generate preview of translated PDF
        progress(0.9, desc="Generating preview...")
        try:
            translated_preview = pdf_preview(str(final_output))
        except Exception as e:
            print(f"Error generating preview: {e}")
            translated_preview = None

    progress(1.0, desc="Translation complete!")
    gr.Info(f"翻译成功！文件已保存在:\n{output_dir}\n- {final_output.name}\n- {final_output_dual.name}")
    return (
        saved_files if saved_files else str(final_output),
        translated_preview,
        gr.update(visible=True),
        gr.update(visible=True),
    )


def load_hotwords():
    hotwords_path = "saved_hotwords.txt"
    if os.path.exists(hotwords_path):
        try:
            with open(hotwords_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""

# Global setup
constructivism_red = gr.themes.Color(
    c50="#FFEEEE",
    c100="#FFCCCC",
    c200="#FFAAAA",
    c300="#FF7777",
    c400="#FF4444",
    c500="#DD0000",  # Strong Soviet Red
    c600="#BB0000",
    c700="#990000",
    c800="#660000",
    c900="#330000",
    c950="#110000",
)

with gr.Blocks(
    title="PDFMathTranslate - PDF Translation with preserved formats",
    theme=gr.themes.Default(
        primary_hue=constructivism_red, spacing_size="lg", radius_size="none"
    ),
    css="""
    body { background-color: #FAFAFA !important; }
    * { font-family: 'Impact', 'Arial Black', sans-serif !important; text-transform: uppercase; }
    .secondary-text {color: #000 !important; font-weight: 900;}
    footer {visibility: hidden}
    .env-warning {color: #DD0000 !important; background: #FFF; padding: 4px; border: 2px solid #000;}
    .env-success {color: #000 !important; background: #FFEA00; padding: 4px; border: 2px solid #000;}
    
    @keyframes sharp-blink {
        0%, 49% { background-color: #FFF; color: #000; }
        50%, 100% { background-color: #DD0000; color: #FFF; }
    }
    
    /* Hard borders everywhere */
    .gradio-container { border: 8px solid #000; box-shadow: 10px 10px 0px #DD0000; background: #FFF !important;}
    
    .input-file {
        border: 4px solid #000 !important;
        border-radius: 0px !important;
        background-color: #FFF !important;
        box-shadow: 4px 4px 0px #000 !important;
        transition: transform 0.1s, box-shadow 0.1s;
    }

    .input-file:hover {
        transform: translate(-2px, -2px);
        box-shadow: 6px 6px 0px #DD0000 !important;
    }

    /* Buttons */
    button.primary {
        background: #DD0000 !important;
        color: #FFF !important;
        border: 4px solid #000 !important;
        border-radius: 0 !important;
        font-weight: 900 !important;
        font-size: 1.5em !important;
        text-shadow: 2px 2px 0px #000;
        box-shadow: 6px 6px 0px #000 !important;
    }
    button.primary:hover {
        background: #000 !important;
        color: #DD0000 !important;
        text-shadow: 2px 2px 0px #FFF;
        box-shadow: 6px 6px 0px #DD0000 !important;
    }

    /* Progress bar */
    .progress-bar-wrap { border-radius: 0px !important; border: 2px solid #000 !important;}
    .progress-bar { border-radius: 0px !important; background-color: #DD0000 !important; }

    /* Headers */
    h1, h2, h3 { color: #000 !important; text-shadow: 3px 3px 0px #DD0000; font-weight: 900 !important; letter-spacing: 2px; }
    """,
) as demo:
    gr.Markdown("# PDFMathTranslate")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 1. FILE & SAVE (文件与保存)")
            with gr.Group():
                file_input = gr.File(
                    label="上传待翻译的PDF",
                    file_count="single",
                    file_types=[".pdf"],
                    type="filepath",
                    elem_classes=["input-file"],
                )
                save_dir = gr.Textbox(
                    label="文件保存路径 (Save Directory)",
                    info="翻译成功后，纯中文版和双语对照版PDF将保存在此目录下",
                    value=r"D:\报账\报账\报销明细\报销明细\YJJ-报销明细\venv",
                )

            gr.Markdown("## 2. TRANSLATION ENGINE (翻译引擎)")
            with gr.Group():
                service = gr.Dropdown(
                    label="Service",
                    info="选择翻译服务。默认已配置为 DeepSeek 大模型。",
                    choices=service_map.keys(),
                    value="OpenAI",
                )
                with gr.Row():
                    model_id = gr.Textbox(
                        label="Model ID",
                        value="deepseek-v4-flash-vision-exp",
                        visible=True,
                    )
                    thinking_level = gr.Dropdown(
                        label="Thinking Level",
                        choices=["none", "low", "medium", "high"],
                        value="none",
                        visible=True,
                    )
                    openai_base_url = gr.Textbox(
                        label="Base URL",
                        value="https://api.deepseek.com",
                        visible=True,
                    )
                openai_api_key = gr.Textbox(
                    label="OpenAI / DeepSeek API Key",
                    type="password",
                    visible=True,
                    value=os.environ.get("DEEPSEEK_API_KEY", ""),
                )
                lang_to = gr.Dropdown(
                    label="Translate to",
                    info="目标语言 (Target Language)",
                    choices=lang_map.keys(),
                    value="Chinese",
                )

            gr.Markdown("## 3. SETTINGS (参数配置)")
            with gr.Group():
                page_range = gr.Radio(
                    ["All", "First", "First 5 pages"],
                    label="Pages",
                    info="选择翻译页数",
                    value="All",
                )
                hotwords = gr.Textbox(
                    label="自定义热词替换 (Hotwords) - 已开启自动记忆",
                    info="格式：英文=中文，多项请换行（例如：Yuying Han=韩玉莹）。",
                    value=load_hotwords,
                    lines=4,
                )
                extra_args = gr.Textbox(
                    label="Advanced Arguments (高级参数)",
                    info="Extra arguments supported in commandline (optional)",
                    value="",
                )
            envs_status = "<span class='env-success'>- Properly configured.</span><br>"

            def details_wrapper(text_markdown):
                text = f""" 
                <details>
                    <summary>Technical details</summary>
                    {text_markdown}
                    - GitHub: <a href="https://github.com/Byaidu/PDFMathTranslate">Byaidu/PDFMathTranslate</a><br>
                    - GUI by: <a href="https://github.com/reycn">Rongxin</a><br>
                    - Version: {__version__}
                </details>"""
                return text

            def env_var_checker(env_var_name: str) -> str:
                if (
                    not os.environ.get(env_var_name)
                    or os.environ.get(env_var_name) == ""
                ):
                    envs_status = f"<span class='env-warning'>- Warning: environmental not found or error ({env_var_name}).</span><br>- Please make sure that the environment variables are properly configured (<a href='https://github.com/Byaidu/PDFMathTranslate'>guide</a>).<br>"
                else:
                    value = str(os.environ.get(env_var_name))
                    envs_status = (
                        "<span class='env-success'>- Properly configured.</span><br>"
                    )
                    if len(value) < 13:
                        envs_status += (
                            f"- Env: <code>{os.environ.get(env_var_name)}</code><br>"
                        )
                    else:
                        envs_status += f"- Env: <code>{value[:13]}***</code><br>"
                return details_wrapper(envs_status)

            def on_select_service(value, evt: gr.EventData):
                model_visibility = gr.update(visible=False)
                api_key_vis = gr.update(visible=False)
                base_url_vis = gr.update(visible=False)
                thinking_level_vis = gr.update(visible=False)
                hotwords_info = gr.update(info="格式：英文=中文，多项请换行（例如：Yuying Han=韩玉莹）。")

                if value == "Google":
                    envs_status = details_wrapper(
                        "<span class='env-success'>- Properly configured.</span><br>"
                    )
                elif value == "DeepL":
                    envs_status = env_var_checker("DEEPL_AUTH_KEY")
                elif value == "DeepLX":
                    envs_status = env_var_checker("DEEPLX_AUTH_KEY")
                elif value == "Azure":
                    envs_status = env_var_checker("AZURE_APIKEY")
                elif value == "OpenAI":
                    model_visibility = gr.update(visible=True)
                    api_key_vis = gr.update(visible=True)
                    base_url_vis = gr.update(visible=True)
                    thinking_level_vis = gr.update(visible=True)
                    envs_status = details_wrapper("<span class='env-success'>- DeepSeek 配置就绪。</span><br>")
                    hotwords_info = gr.update(info="【AI 智能模式】请直接填入需要确保正确的中文名（例如：韩玉莹 韩前程 秦慧民），用空格或换行隔开即可。")
                elif value == "Ollama":
                    model_visibility = gr.update(visible=True, value="gemma2")
                    envs_status = env_var_checker("OLLAMA_HOST")
                    hotwords_info = gr.update(info="【AI 智能模式】请直接填入需要确保正确的中文名（例如：韩玉莹 韩前程 秦慧民），用空格或换行隔开即可。")
                else:
                    envs_status = "<span class='env-warning'>- Warning: model not in the list.</span><br>- Please report via (<a href='https://github.com/Byaidu/PDFMathTranslate'>guide</a>).<br>"
                return envs_status, model_visibility, api_key_vis, base_url_vis, hotwords_info, thinking_level_vis

            output_title = gr.Markdown("## Translated", visible=False)
            output_file = gr.File(label="Download Translation (纯中文版 / 双语对照版)", visible=False, file_count="multiple")
            translate_btn = gr.Button("Translate", variant="primary", visible=False)
            tech_details_tog = gr.Markdown(
                details_wrapper(envs_status),
                elem_classes=["secondary-text"],
            )
            service.select(on_select_service, service, [tech_details_tog, model_id, openai_api_key, openai_base_url, hotwords, thinking_level])

        with gr.Column(scale=2):
            gr.Markdown("## Preview")
            preview = gr.Image(label="Document Preview", visible=True)

    # Event handlers
    file_input.upload(
        upload_file,
        inputs=[file_input, service],
        outputs=[file_input, preview, translate_btn],
    )

    translate_btn.click(
        translate,
        inputs=[file_input, service, model_id, lang_to, page_range, extra_args, hotwords, save_dir, openai_api_key, openai_base_url, thinking_level],
        outputs=[
            output_file,
            preview,
            output_file,
            output_title,
        ],
    )


def setup_gui(share=False):
    # Prevent system proxies (Clash, v2ray, etc.) from intercepting local loopback requests
    for k in ["NO_PROXY", "no_proxy"]:
        curr = os.environ.get(k, "")
        local_hosts = "localhost,127.0.0.1,0.0.0.0"
        os.environ[k] = f"{curr},{local_hosts}" if curr else local_hosts

    try:
        demo.launch(server_name="127.0.0.1", debug=True, inbrowser=True, share=share)
    except Exception as e:
        print(f"Error launching GUI using 127.0.0.1: {e}")
        try:
            demo.launch(server_name="0.0.0.0", debug=True, inbrowser=True, share=share)
        except Exception as e2:
            print(f"Error launching GUI using 0.0.0.0: {e2}")
            if share:
                demo.launch(debug=True, inbrowser=True, share=True)
            else:
                raise e2

# For auto-reloading while developing
if __name__ == "__main__":
    setup_gui()
