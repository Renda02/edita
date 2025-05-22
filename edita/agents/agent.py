class Agent:
    def __init__(self, name, instructions, tools):
        self.name = name
        self.instructions = instructions
        self.tools = tools

    async def run(self, prompt):
        responses = []

        for tool in self.tools:
            if hasattr(tool, "search"):
                result = tool.search(prompt)
                responses.append(f"- {tool.__class__.__name__}: {result}")

        response_text = (
            f"**{self.name} Response**\n\n"
            f"{self.instructions.strip()}\n\n"
            f"### Sources:\n" + "\n".join(responses)
        )

        return response_text
