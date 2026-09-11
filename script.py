# 这是一个示例 Python 脚本。

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。

def azhe(self,s,k):
    pinlv=0
    zuihou=[]
    for _ in range(s):
        if pinlv!=1:
            chushi=[]
            zuida=0
            shuicao=[]
            zuibang=[]
            i=0
            jishu=0
            while i<=len(k)-1:
                chushi[i].append(k[i],k[i+1])
                if chushi[i]==shuicao[k]:
                    zuida[k]+=1
                    i+=1
                else:
                    shuicao.append(chushi[i])
                zuida=max(shuicao[i],zuida)
                pinlv=zuida
                i+=1
                jishu+=1
            for w in range(jishu):
                zuibang.append(chushi[w])
            zuibang,k=k,zuibang
            return pinlv
        else:
            return k
        return k