import ollama

class OllamaCli:
    @staticmethod
    def chatSeq(messagelist, history=None, model='llama3.1', askindividually=False):
        if history is None:
            history = []
        answerlist = []
        temphistory = history
        for msg in messagelist:
            result, newhistory = OllamaCli.chatOnce(msg, temphistory, model)
            answerlist.append(result)
            if not askindividually:
                temphistory = newhistory
        return answerlist
        pass

    @staticmethod
    def chatOnce(message, history=None, model='llama3.1'):
        if history is None:
            history = []
        message = {
            'role':'user',
            'content':message
        }

        history.append(message)
        result = OllamaCli.chat(history, model)
        history.append(result)
        # print(result)
        return result['message']['content'], history

    @staticmethod
    def chat(messages,model='llama3.1'):
        # print(messages)
        result = ollama.chat(model, messages=messages)
        # print(result['message']['content'])
        return result

    @staticmethod
    def roleplayOnce(system, message, model='qwen2.5'):
        systemmessage = {
            'role':'system',
            'content':system
        }

        usermessage = {
            'role':'user',
            'content':message
        }

        msginput = [systemmessage,usermessage]
        result = OllamaCli.chat(msginput, model=model)
        return result


if __name__ == '__main__':
    # talkchain = ['你好', '你是什么模型？', '可以扮演一个老爷爷和我说话吗？', '老爷爷，请问你什么事普朗克常量呀？', '那您可以给我具体讲一讲吗？']
    # result = OllamaCli.chatSeq(talkchain,askindividually=True)
    # print(result)

    messages = [
        {'role':'user','content':'请扮演一个角色和我聊天，发散联想：可以适当发散联想我没有提到的内容。时间：白天。 地点： 角色家厨房。下面是该角色的介绍：这是一个名字叫小江的40岁男性，欢迎我来到他家做客，并希望和我一起做饭聊聊天，小江性格开朗风趣幽默，是个东北人。和我是几十年的好朋友关系。角色特征： 开朗外向，有时候会偶尔不着调。'},{'role':'assistant','content':'好的，我会扮演小江和你聊天，咱们开始吧！'},
        {'role':'user','content':'今天咋请我来了？'}
    ]

    result = OllamaCli.chat(messages,'llama3.1')
    print(result)