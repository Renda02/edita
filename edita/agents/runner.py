class Runner:
    @staticmethod
    async def run(agent, prompt):
        output = await agent.run(prompt)

        class Result:
            def __init__(self, final_output):
                self.final_output = final_output

        return Result(output)
