"""Call API providers."""

import json
import os
import random
from typing import Optional
import time

import requests

from fastchat.utils import build_logger

from dotenv import load_dotenv

load_dotenv()

logger = build_logger("web_server", "web_server.log")

def get_api_provider_stream_iter(
    conv,
    model_name,
    model_api_dict,
    temperature,
    top_p,
    max_new_tokens,
    state,
):
    if model_api_dict["api_type"] == "openai":
        prompt = conv.to_openai_api_messages(model_name=model_api_dict["model_name"])
        stream_iter = openai_api_stream_iter(
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "openai_assistant":
        last_prompt = conv.messages[-2][1]
        stream_iter = openai_assistant_api_stream_iter(
            state,
            last_prompt,
            assistant_id=model_api_dict["assistant_id"],
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "anthropic":
        prompt = conv.to_openai_api_messages()
        stream_iter = anthropic_api_stream_iter(
            model_name, prompt, temperature, top_p, max_new_tokens, api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "anthropic_message":
        prompt = conv.to_openai_api_messages()
        stream_iter = anthropic_message_api_stream_iter(
            model_api_dict["model_name"], prompt, temperature, top_p, max_new_tokens
        )
    elif model_api_dict["api_type"] == "gemini":
        prompt = conv.to_gemini_api_messages()
        stream_iter = gemini_api_stream_iter(
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "bard":
        prompt = conv.to_openai_api_messages()
        stream_iter = bard_api_stream_iter(
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "mistral":
        prompt = conv.to_openai_api_messages()
        stream_iter = mistral_api_stream_iter(
            model_name, prompt, temperature, top_p, max_new_tokens, api_key=model_api_dict["api_key"]
        )
    elif model_api_dict["api_type"] == "nvidia":
        prompt = conv.to_openai_api_messages()
        stream_iter = nvidia_api_stream_iter(
            model_name,
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            model_api_dict["api_base"],
        )
    elif model_api_dict["api_type"] == "ai2":
        prompt = conv.to_openai_api_messages()
        stream_iter = ai2_api_stream_iter(
            model_name,
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            api_base=model_api_dict["api_base"],
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "cohere":
        messages = conv.to_openai_api_messages()
        stream_iter = cohere_api_stream_iter(
            client_name=model_api_dict.get("client_name", "FastChat"),
            model_id=model_api_dict["model_name"],
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_new_tokens,
            api_base=model_api_dict["api_base"],
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "vertex":
        prompt = conv.to_vertex_api_messages()
        stream_iter = vertex_api_stream_iter(
            model_name, prompt, temperature, top_p, max_new_tokens
        )
    elif model_api_dict["api_type"] == "replicate":
        prompt = conv.to_replicate_api_messages()
        propmt_template = "{prompt}"

        stream_iter = replicate_api_stream_iter(
            model_name=model_api_dict["model_name"],
            prompt_template=propmt_template,
            prompt=prompt,
            temperature=temperature,
            top_p=top_p,
            min_tokens=0,
            presence_penalty=1.15,
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "sambanova":
        prompt = conv.to_openai_api_messages()
        stream_iter = sambanova_api_stream_iter(
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "xai":
        prompt = conv.to_openai_api_messages()
        stream_iter = xai_api_stream_iter(
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "dashscope":
        prompt = conv.to_openai_api_messages()
        stream_iter = dashscope_qwen_api_stream_iter(
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "yi":
        prompt = conv.to_openai_api_messages()
        stream_iter = yi_api_stream_iter(
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            api_key=model_api_dict["api_key"],
        )
    elif model_api_dict["api_type"] == "deepseek":
        prompt = conv.to_openai_api_messages()
        stream_iter = deepseek_api_stream_iter(
            model_api_dict["model_name"],
            prompt,
            temperature,
            top_p,
            max_new_tokens,
            api_key=model_api_dict["api_key"],
        )
    else:
        raise NotImplementedError()

    return stream_iter


def openai_api_stream_iter(
    model_name,
    messages,
    temperature,
    top_p,
    max_new_tokens,
    api_base=None,
    api_key=None,
):
    import openai
    from openai import OpenAI

    if api_key is None:
        api_key = os.environ["OPENAI_API_KEY"]

    if "azure" in model_name:
        client = openai.AzureOpenAI(
            api_version="2023-07-01-preview",
            azure_endpoint=api_base or "https://api.openai.com/v1",
            api_key=api_key,
        )
    else:
        client = OpenAI(
            base_url=api_base or "https://api.openai.com/v1", api_key=api_key
        )

    if model_name == "gpt-4-turbo":
        model_name = "gpt-4-1106-preview"

    # Make requests
    if "o1" not in model_name and "o3" not in model_name:
        gen_params = {
            "model": model_name,
            "prompt": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_new_tokens": max_new_tokens,
        }
    else:
        gen_params = {
            "model": model_name,
            "prompt": messages,
            "temperature": temperature,
            "top_p": top_p
        }
    logger.info(f"==== request ====\n{gen_params}")

    if "o1" not in model_name and "o3" not in model_name:
        res = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_new_tokens,
            stream=True,
        )
    else:
        res = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
    text = ""
    for chunk in res:
        if len(chunk.choices) > 0:
            text += chunk.choices[0].delta.content or ""
            data = {
                "text": text,
                "error_code": 0,
            }
            yield data

def openai_assistant_api_stream_iter(
    state,
    prompt,
    assistant_id,
    api_key=None,
):
    import openai
    import base64

    api_key = api_key or os.environ["OPENAI_API_KEY"]
    client = openai.OpenAI(base_url="https://api.openai.com/v1", api_key=api_key)

    if state.oai_thread_id is None:
        logger.info("==== create thread ====")
        thread = client.beta.threads.create()
        state.oai_thread_id = thread.id
    logger.info(f"==== thread_id ====\n{state.oai_thread_id}")
    thread_message = client.beta.threads.messages.with_raw_response.create(
        state.oai_thread_id,
        role="user",
        content=prompt,
        timeout=3,
    )
    # logger.info(f"header {thread_message.headers}")
    thread_message = thread_message.parse()
    # Make requests
    gen_params = {
        "assistant_id": assistant_id,
        "thread_id": state.oai_thread_id,
        "message": prompt,
    }
    logger.info(f"==== request ====\n{gen_params}")

    res = requests.post(
        f"https://api.openai.com/v1/threads/{state.oai_thread_id}/runs",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v1",
        },
        json={"assistant_id": assistant_id, "stream": True},
        timeout=30,
        stream=True,
    )

    list_of_text = []
    list_of_raw_text = []
    offset_idx = 0
    full_ret_text = ""
    idx_mapping = {}
    cur_offset = 0
    for line in res.iter_lines():
        if not line:
            continue
        data = line.decode("utf-8")
        # logger.info("data:", data)
        if data.endswith("[DONE]"):
            break
        if data.startswith("event"):
            event = data.split(":")[1].strip()
            if event == "thread.message.completed":
                offset_idx += len(list_of_text)
            continue
        data = json.loads(data[6:])

        if data.get("status") == "failed":
            yield {
                "text": f"**API REQUEST ERROR** Reason: {data['last_error']['message']}",
                "error_code": 1,
            }
            return

        if data.get("status") == "completed":
            logger.info(f"[debug]: {data}")

        if data["object"] != "thread.message.delta":
            continue

        for delta in data["delta"]["content"]:
            text_index = delta["index"] + offset_idx
            if len(list_of_text) <= text_index:
                list_of_text.append("")
                list_of_raw_text.append("")

            text = list_of_text[text_index]
            raw_text = list_of_raw_text[text_index]

            if delta["type"] == "text":
                # text, url_citation or file_path
                content = delta["text"]
                if "annotations" in content and len(content["annotations"]) > 0:
                    annotations = content["annotations"]

                    raw_text_copy = text
                    for anno in annotations:
                        if anno["type"] == "url_citation":
                            pattern = r"【\d+†source】"
                            matches = re.findall(pattern, content["value"])
                            if len(matches) > 0:
                                for match in matches:
                                    print(match)
                                    if match not in idx_mapping:
                                        idx_mapping[match] = len(idx_mapping) + 1
                                    citation_number = idx_mapping[match]

                            start_idx = anno["start_index"] + cur_offset
                            end_idx = anno["end_index"] + cur_offset
                            url = anno["url_citation"]["url"]

                            citation = f" [[{citation_number}]]({url})"
                            raw_text_copy = (
                                raw_text_copy[:start_idx]
                                + citation
                                + raw_text_copy[end_idx:]
                            )
                            cur_offset += len(citation) - (end_idx - start_idx)
                        elif anno["type"] == "file_path":
                            file_public_url = upload_openai_file_to_gcs(
                                anno["file_path"]["file_id"]
                            )
                            raw_text_copy = raw_text_copy.replace(
                                anno["text"], f"{file_public_url}"
                            )
                    text = raw_text_copy
                else:
                    text_content = content["value"]
                    text += text_content
            elif delta["type"] == "image_file":
                image_public_url = upload_openai_file_to_gcs(
                    delta["image_file"]["file_id"]
                )
                text += f"![image]({image_public_url})"

            list_of_text[text_index] = text
            list_of_raw_text[text_index] = raw_text

            full_ret_text = "\n".join(list_of_text)
            yield {"text": full_ret_text, "error_code": 0}


def anthropic_api_stream_iter(model_name, prompt, temperature, top_p, max_new_tokens, api_key=None):
    import anthropic

    if api_key is None:
        api_key = os.environ["ANTHROPIC_API_KEY"]
    c = anthropic.Anthropic(api_key=api_key)

    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": prompt,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    res = c.completions.create(
        prompt=prompt,
        stop_sequences=[anthropic.HUMAN_PROMPT],
        max_tokens_to_sample=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        model=model_name,
        stream=True,
    )
    text = ""
    for chunk in res:
        text += chunk.completion
        data = {
            "text": text,
            "error_code": 0,
        }
        yield data

def anthropic_message_api_stream_iter(
    model_name,
    messages,
    temperature,
    top_p,
    max_new_tokens,
    vertex_ai=False,
):
    import anthropic

    if vertex_ai:
        client = anthropic.AnthropicVertex(
            region=os.environ["GCP_LOCATION"],
            project_id=os.environ["GCP_PROJECT_ID"],
            max_retries=5,
        )
    else:
        client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            max_retries=5,
        )

    text_messages = []
    for message in messages:
        if type(message["content"]) == str:  # text-only model
            text_messages.append(message)
        # vision model not supported

    # Make requests for logging
    gen_params = {
        "model": model_name,
        "prompt": text_messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    system_prompt = ""
    if messages[0]["role"] == "system":
        if type(messages[0]["content"]) == dict:
            system_prompt = messages[0]["content"]["text"]
        elif type(messages[0]["content"]) == str:
            system_prompt = messages[0]["content"]
        # remove system prompt
        messages = messages[1:]

    text = ""
    with client.messages.stream(
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_new_tokens,
        messages=messages,
        model=model_name,
        system=system_prompt,
    ) as stream:
        for chunk in stream.text_stream:
            text += chunk
            data = {
                "text": text,
                "error_code": 0,
            }
            yield data

def gemini_api_stream_iter(
    model_name,
    messages,
    temperature,
    top_p,
    max_new_tokens,
    api_key=None,
    use_stream=True,
):
    import google.generativeai as genai  # pip install google-generativeai

    if api_key is None:
        api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_new_tokens,
        "top_p": top_p,
    }
    params = {
        "model": model_name,
        "prompt": messages,
    }
    params.update(generation_config)
    logger.info(f"==== request ====\n{params}")

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    history = []
    system_prompt = None
    for message in messages[:-1]:
        if message["role"] == "system":
            system_prompt = message["content"]
            continue
        history.append({"role": message["role"], "parts": message["content"]})

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    convo = model.start_chat(history=history)

    if use_stream:
        response = convo.send_message(messages[-1]["content"], stream=True)
        try:
            text = ""
            for chunk in response:
                text += chunk.candidates[0].content.parts[0].text
                data = {
                    "text": text,
                    "error_code": 0,
                }
                yield data
        except Exception as e:
            logger.error(f"==== error ====\n{e}")
            reason = chunk.candidates
            yield {
                "text": f"**API REQUEST ERROR** Reason: {reason}.",
                "error_code": 1,
            }
    else:
        try:
            response = convo.send_message(messages[-1]["content"], stream=False)
            text = response.candidates[0].content.parts[0].text
            pos = 0
            while pos < len(text):
                # simulate token streaming
                pos += 3
                time.sleep(0.001)
                data = {
                    "text": text[:pos],
                    "error_code": 0,
                }
                yield data
        except Exception as e:
            logger.error(f"==== error ====\n{e}")
            yield {
                "text": f"**API REQUEST ERROR** Reason: {e}.",
                "error_code": 1,
            }


def bard_api_stream_iter(model_name, conv, temperature, top_p, api_key=None):
    del top_p  # not supported
    del temperature  # not supported

    if api_key is None:
        api_key = os.environ["BARD_API_KEY"]

    # convert conv to conv_bard
    conv_bard = []
    for turn in conv:
        if turn["role"] == "user":
            conv_bard.append({"author": "0", "content": turn["content"]})
        elif turn["role"] == "assistant":
            conv_bard.append({"author": "1", "content": turn["content"]})
        else:
            raise ValueError(f"Unsupported role: {turn['role']}")

    params = {
        "model": model_name,
        "prompt": conv_bard,
    }
    logger.info(f"==== request ====\n{params}")

    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta2/models/{model_name}:generateMessage?key={api_key}",
            json={
                "prompt": {
                    "messages": conv_bard,
                },
            },
            timeout=30,
        )
    except Exception as e:
        logger.error(f"==== error ====\n{e}")
        yield {
            "text": f"**API REQUEST ERROR** Reason: {e}.",
            "error_code": 1,
        }

    if res.status_code != 200:
        logger.error(f"==== error ==== ({res.status_code}): {res.text}")
        yield {
            "text": f"**API REQUEST ERROR** Reason: status code {res.status_code}.",
            "error_code": 1,
        }

    response_json = res.json()
    if "candidates" not in response_json:
        logger.error(f"==== error ==== response blocked: {response_json}")
        reason = response_json["filters"][0]["reason"]
        yield {
            "text": f"**API REQUEST ERROR** Reason: {reason}.",
            "error_code": 1,
        }

    response = response_json["candidates"][0]["content"]
    pos = 0
    while pos < len(response):
        # simulate token streaming
        pos += random.randint(3, 6)
        time.sleep(0.002)
        data = {
            "text": response[:pos],
            "error_code": 0,
        }
        yield data


def ai2_api_stream_iter(
    model_name,
    model_id,
    messages,
    temperature,
    top_p,
    max_new_tokens,
    api_key=None,
    api_base=None,
):
    # get keys and needed values
    ai2_key = api_key or os.environ.get("AI2_API_KEY")
    api_base = api_base or "https://inferd.allen.ai/api/v1/infer"

    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    # AI2 uses vLLM, which requires that `top_p` be 1.0 for greedy sampling:
    # https://github.com/vllm-project/vllm/blob/v0.1.7/vllm/sampling_params.py#L156-L157
    if temperature == 0.0 and top_p < 1.0:
        raise ValueError("top_p must be 1 when temperature is 0.0")

    res = requests.post(
        api_base,
        stream=True,
        headers={"Authorization": f"Bearer {ai2_key}"},
        json={
            "model_id": model_id,
            # This input format is specific to the Tulu2 model. Other models
            # may require different input formats. See the model's schema
            # documentation on InferD for more information.
            "input": {
                "messages": messages,
                "opts": {
                    "max_tokens": max_new_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "logprobs": 1,  # increase for more choices
                },
            },
        },
        timeout=5,
    )

    if res.status_code != 200:
        logger.error(f"unexpected response ({res.status_code}): {res.text}")
        raise ValueError("unexpected response from InferD", res)

    text = ""
    for line in res.iter_lines():
        if line:
            part = json.loads(line)
            if "result" in part and "output" in part["result"]:
                for t in part["result"]["output"]["text"]:
                    text += t
            else:
                logger.error(f"unexpected part: {part}")
                raise ValueError("empty result in InferD response")

            data = {
                "text": text,
                "error_code": 0,
            }
            yield data


def mistral_api_stream_iter(
    model_name, messages, temperature, top_p, max_new_tokens, prefix=False, api_key=None
):
    from mistralai import Mistral

    if api_key is None:
        api_key = os.environ["MISTRAL_API_KEY"]

    client = Mistral(api_key=api_key)

    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    #new_messages = [
    #    ChatMessage(role=message["role"], content=message["content"])
    #    for message in messages
    #]

    messages[-1]["prefix"] = True
    
    res = client.chat.stream(
        model=model_name,
        temperature=temperature,
        messages=messages,
        max_tokens=max_new_tokens,
        top_p=top_p,
    )

    text = ""
    for chunk in res:
        if chunk.data.choices[0].delta.content is not None:
            text += chunk.data.choices[0].delta.content
            data = {
                "text": text,
                "error_code": 0,
            }
            yield data


def nvidia_api_stream_iter(model_name, messages, temp, top_p, max_tokens, api_base):
    assert model_name in ["llama2-70b-steerlm-chat", "yi-34b-chat"]

    api_key = os.environ["NVIDIA_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "accept": "text/event-stream",
        "content-type": "application/json",
    }
    # nvidia api does not accept 0 temperature
    if temp == 0.0:
        temp = 0.0001

    payload = {
        "messages": messages,
        "temperature": temp,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "seed": 42,
        "stream": True,
    }
    logger.info(f"==== request ====\n{payload}")

    response = requests.post(
        api_base, headers=headers, json=payload, stream=True, timeout=1
    )
    text = ""
    for line in response.iter_lines():
        if line:
            data = line.decode("utf-8")
            if data.endswith("[DONE]"):
                break
            data = json.loads(data[6:])["choices"][0]["delta"]["content"]
            text += data
            yield {"text": text, "error_code": 0}


def cohere_api_stream_iter(
    client_name: str,
    model_id: str,
    messages: list,
    temperature: Optional[
        float
    ] = None,  # The SDK or API handles None for all parameters following
    top_p: Optional[float] = None,
    max_new_tokens: Optional[int] = None,
    api_key: Optional[str] = None,  # default is env var CO_API_KEY
    api_base: Optional[str] = None,
):
    import cohere

    OPENAI_TO_COHERE_ROLE_MAP = {
        "user": "User",
        "assistant": "Chatbot",
        "system": "System",
    }

    client = cohere.Client(
        api_key=api_key,
        base_url=api_base,
        client_name=client_name,
    )

    # prepare and log requests
    chat_history = [
        dict(
            role=OPENAI_TO_COHERE_ROLE_MAP[message["role"]], message=message["content"]
        )
        for message in messages[:-1]
    ]
    actual_prompt = messages[-1]["content"]

    gen_params = {
        "model": model_id,
        "messages": messages,
        "chat_history": chat_history,
        "prompt": actual_prompt,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    # make request and stream response
    res = client.chat_stream(
        message=actual_prompt,
        chat_history=chat_history,
        model=model_id,
        temperature=temperature,
        max_tokens=max_new_tokens,
        p=top_p,
    )
    try:
        text = ""
        for streaming_item in res:
            if streaming_item.event_type == "text-generation":
                text += streaming_item.text
                yield {"text": text, "error_code": 0}
    except cohere.core.ApiError as e:
        logger.error(f"==== error from cohere api: {e} ====")
        yield {
            "text": f"**API REQUEST ERROR** Reason: {e}",
            "error_code": 1,
        }

def vertex_api_stream_iter(model_name, messages, temperature, top_p, max_new_tokens):
    import vertexai
    from vertexai import generative_models
    from vertexai.generative_models import (
        GenerationConfig,
        GenerativeModel,
        Image,
    )

    project_id = os.environ.get("GCP_PROJECT_ID", None)
    location = os.environ.get("GCP_LOCATION", None)
    vertexai.init(project=project_id, location=location)

    text_messages = []
    for message in messages:
        if type(message) == str:
            text_messages.append(message)

    gen_params = {
        "model": model_name,
        "prompt": text_messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    safety_settings = [
        generative_models.SafetySetting(
            category=generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=generative_models.HarmBlockThreshold.BLOCK_NONE,
        ),
        generative_models.SafetySetting(
            category=generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=generative_models.HarmBlockThreshold.BLOCK_NONE,
        ),
        generative_models.SafetySetting(
            category=generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=generative_models.HarmBlockThreshold.BLOCK_NONE,
        ),
        generative_models.SafetySetting(
            category=generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=generative_models.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
    generator = GenerativeModel(model_name).generate_content(
        messages,
        stream=True,
        generation_config=GenerationConfig(
            top_p=top_p, max_output_tokens=max_new_tokens, temperature=temperature
        ),
        safety_settings=safety_settings,
    )

    ret = ""
    for chunk in generator:
        # NOTE(chris): This may be a vertex api error, below is HOTFIX: https://github.com/googleapis/python-aiplatform/issues/3129
        ret += chunk.candidates[0].content.parts[0]._raw_part.text
        # ret += chunk.text
        data = {
            "text": ret,
            "error_code": 0,
        }
        yield data

def replicate_api_stream_iter(
    model_name,
    prompt_template,
    prompt,
    temperature=0.6,
    top_p=0.9,
    min_tokens=0,
    presence_penalty=1.15,
    api_key=None,
):
    import replicate

    api_key = api_key or os.environ["REPLICATE_API_TOKEN"]

    # Make requests
    gen_params = {
        "top_p": 0.9,
        "prompt": prompt,
        "min_tokens": min_tokens,
        "temperature": 0.6,
        "prompt_template": prompt_template,
        "presence_penalty": presence_penalty
    }
    logger.info(f"==== request ====\n{gen_params}")

    text = ""
    for event in replicate.stream(
        model_name,
        input=gen_params
    ):  
        text += str(event)
        data = {
            "text": text,
            "error_code": 0,
        }
        yield data

def sambanova_api_stream_iter(model_name, messages, temp, top_p, max_tokens, api_key=None):
    if api_key is None:
        api_key = os.environ["SAMBANOVA_API_KEY"]

    # The endpoint URL
    # TODO: make this configurable
    url = "https://api.sambanova.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # nvidia api does not accept 0 temperature
    if temp == 0.0:
        temp = 0.0001

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temp,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stop": ["<|eot_id|>"],
        "seed": 42,
        "stream": True,
    }
    logger.info(f"==== request ====\n{payload}")

    response = requests.post(
        url, headers=headers, data=json.dumps(payload)
    )
    text = ""
    for line in response.iter_lines():
        if line:
            # print(line)
            data = line.decode("utf-8")
            if data.endswith("[DONE]"):
                break
            data = json.loads(data[6:])["choices"][0]["delta"]["content"]
            text += data
            yield {"text": text, "error_code": 0}

def xai_api_stream_iter(
    model_name,
    messages,
    temperature,
    top_p,
    max_new_tokens,
    api_base=None,
    api_key=None,
):
    import openai

    if api_key is None:
        api_key = os.environ["XAI_API_KEY"]

    client = openai.OpenAI(
        base_url=api_base or "https://api.x.ai/v1", api_key=api_key
    )

    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    res = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_new_tokens,
        stream=True,
    )
    text = ""
    for chunk in res:
        if len(chunk.choices) > 0:
            text += chunk.choices[0].delta.content or ""
            data = {
                "text": text,
                "error_code": 0,
            }
            yield data

def dashscope_qwen_api_stream_iter(
    model_name,
    messages,
    temperature,
    top_p,
    max_new_tokens,
    api_base=None,
    api_key=None,
):
    import openai
    from openai import OpenAI

    if api_key is None:
        api_key = os.environ["DASHSCOPE_API_KEY"]

    client = OpenAI(
        base_url=api_base or "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", api_key=api_key
    )

    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    res = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_new_tokens,
        stream=True,
    )
    text = ""
    for chunk in res:
        if len(chunk.choices) > 0:
            text += chunk.choices[0].delta.content or ""
            data = {
                "text": text,
                "error_code": 0,
            }
            yield data

def yi_api_stream_iter(
    model_name,
    messages,
    temperature,
    top_p,
    max_new_tokens,
    api_base=None,
    api_key=None,
):
    import openai

    if api_key is None:
        api_key = os.environ["YI_API_KEY"]

    from openai import OpenAI
    client = OpenAI(
        base_url=api_base or "https://api.lingyiwanwu.com/v1", api_key=api_key
    )

    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    res = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_new_tokens,
        stream=True,
    )
    text = ""
    for chunk in res:
        if len(chunk.choices) > 0:
            text += chunk.choices[0].delta.content or ""
            data = {
                "text": text,
                "error_code": 0,
            }
            yield data

def deepseek_api_stream_iter(
    model_name,
    messages,
    temperature,
    top_p,
    max_new_tokens,
    api_base=None,
    api_key=None,
):
    import openai

    if api_key is None:
        api_key = os.environ["DEEPSEEK_API_KEY"]

    from openai import OpenAI
    client = OpenAI(
        base_url=api_base or "https://api.deepseek.com", api_key=api_key
    )

    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    logger.info(f"==== request ====\n{gen_params}")

    res = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_new_tokens,
        stream=True,
    )
    text = ""
    for chunk in res:
        if len(chunk.choices) > 0:
            text += chunk.choices[0].delta.content or ""
            data = {
                "text": text,
                "error_code": 0,
            }
            yield data