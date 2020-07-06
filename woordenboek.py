

def func(**kwargs):

    for k, v in kwargs.items():
        print(f"{k} is {v}  ")


func(name='Fred', age="37")
