from agent import app
from langchain_core.messages import HumanMessage
from langgraph.types import Command

def run():
    config = {"configurable": {"thread_id": "user-1"}}
    print("🏠 Smart Home Agent — type 'exit' to quit")

    while True:
        user_input = input("\n> ")
        if user_input.strip().lower() == "exit":
            break

        result = app.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        # لو فيه interrupt، اسأل المستخدم فعليًا وانتظر رده
        while "__interrupt__" in result:
            question = result["__interrupt__"][0].value["question"]
            print(f"\n⚠️  {question}")
            confirm_input = input("Type 'yes' to confirm, anything else to cancel: ")
            decision = "yes" if confirm_input.strip().lower() == "yes" else "no"
            result = app.invoke(Command(resume=decision), config=config)

        print("\nAssistant:", result["messages"][-1].content)

if __name__ == "__main__":
    run()