from client.llm.openai_client import get_openai_client,get_openai_model

def test_openai():
    client=get_openai_client()
    model=get_openai_model()


    response=client.chat.completions.create(
        model=model,
        messages=[
            {
                "role":"user","content":"hi"
            }
        ],
        max_tokens=5,
        temperature=0,
    )
    

    reply=response.choices[0].message.content

    print("success")
    print("model reply:",repr(reply))


if __name__=="__main__":
    test_openai()

