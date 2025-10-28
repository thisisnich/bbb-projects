# # myInt = 8
# # myFloat = 8.0
# # myString = "Preo is so handsome"

# # print (f'integer: {myInt}')
# # print (f'float: {myFloat}')
# # print (f'String: {myString}')
# # def testFunction():
    
# #     print("This is a test function")
# #     return 10
# # testFunction()
# # print(testFunction())
    
# # def myFirstFunctionWithArguments(name, greeting):
# #     print(f"Hello, {name}! {greeting}")
# #     return 20
# # myFirstFunctionWithArguments("John", "Good morning")
# # print(myFirstFunctionWithArguments("John", "Good morning"))

# # def sum(a, b):
# #     return a+b

# # print(sum(1, 2))
# # myFirstFunctionWithArguments("John", "Good morning")
# # myFirstFunctionWithArguments("Johnson", "Happy birthday")

# myset = {"alex", "john", "jane", "jim", "jill"}
# mydict = {"name1": "alex", "name2": "john", "name3": "jane", "name4": "jim", "name5": "jill"}
# print (myset)
# print (mydict)
# mydict.update({"name6": "jim"})
# print(mydict)
# myset.add("mike")
# myset.remove("jane")
# print(myset)

import mymodule

mymodule.greet("Jackery")
StudentName = mymodule.StudentInfo["name"]
print(StudentName)

mymodule.greet(StudentName)