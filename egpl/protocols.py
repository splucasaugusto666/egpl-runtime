"""Provider-neutral request/response codecs. Transport is explicitly caller-owned."""
from .verifiers import bounded_text

PROTOCOLS = ('openai-chat','openai-compatible','anthropic','gemini','ollama')


def request_body(protocol,model,prompt,max_tokens):
    if protocol not in PROTOCOLS:
        raise ValueError('unsupported protocol')
    if not bounded_text(model).strip() or len(model)>256:
        raise ValueError('invalid model')
    bounded_text(prompt)
    if type(max_tokens) is not int or not 1<=max_tokens<=8192:
        raise ValueError('invalid requested output limit')
    if protocol in ('openai-chat','openai-compatible'):
        key = 'max_completion_tokens' if protocol=='openai-chat' else 'max_tokens'
        return {'model':model,'messages':[{'role':'user','content':prompt}],key:max_tokens,'stream':False}
    if protocol=='anthropic':
        return {'model':model,'max_tokens':max_tokens,'messages':[{'role':'user','content':prompt}],'stream':False}
    if protocol=='gemini':
        return {'contents':[{'role':'user','parts':[{'text':prompt}]}],
                'generationConfig':{'maxOutputTokens':max_tokens}}
    return {'model':model,'prompt':prompt,'stream':False,'options':{'num_predict':max_tokens}}


def response_text(protocol,payload):
    """Extract only public final text; reject incomplete or non-text responses."""
    if protocol not in PROTOCOLS or not isinstance(payload,dict) or 'error' in payload:
        raise ValueError('invalid response')
    try:
        if protocol in ('openai-chat','openai-compatible'):
            choice=payload['choices'][0]
            message=choice['message']
            if choice['finish_reason']!='stop' or message.get('refusal') or message.get('tool_calls') or message.get('function_call'):
                raise ValueError('incomplete or non-text response')
            result=message['content']
        elif protocol=='anthropic':
            if payload['stop_reason'] not in ('end_turn','stop_sequence'):
                raise ValueError('incomplete or non-text response')
            result=''.join(p['text'] for p in payload['content'] if p['type']=='text')
        elif protocol=='gemini':
            choice=payload['candidates'][0]
            if choice['finishReason']!='STOP':
                raise ValueError('incomplete or non-text response')
            result=''.join(p['text'] for p in choice['content']['parts']
                           if 'text' in p and not p.get('thought',False))
        else:
            if payload['done'] is not True or payload.get('done_reason','stop')!='stop':
                raise ValueError('incomplete response')
            result=payload['response']
        bounded_text(result)
        if not result.strip():
            raise ValueError('no final text')
        return result
    except (KeyError,IndexError,TypeError,AttributeError,RecursionError) as exc:
        raise ValueError('malformed response') from exc


class WireAdapter:
    """Invoke an authorized caller transport; no credentials or network logic here."""
    def __init__(self,protocol,model,transport,*,max_tokens=256):
        request_body(protocol,model,'',max_tokens)
        if not callable(transport):
            raise ValueError('transport must be callable')
        self.protocol,self.model,self.transport,self.max_tokens=protocol,model,transport,max_tokens

    def __call__(self,prompt,feedback,attempt):
        body=request_body(self.protocol,self.model,prompt+'\n'+feedback,self.max_tokens)
        try:
            return response_text(self.protocol,self.transport(self.protocol,self.model,body))
        except (OSError,ValueError) as exc:
            raise StopIteration from exc
