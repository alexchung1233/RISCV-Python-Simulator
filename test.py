import RISCV_Simulator.Instruction as Instruction
import RISCV_Simulator.PipelineSimulator as PipelineSimulator


def parse(self, s):
    # splits strings into tokens
    s = s.split()

    # get instruction type from first element
    instr = s[0]

    # if rtype then make into a rtype instruction
    if instr in self.instructionSet['rtype']:
        return self.createRTypeInstruction(s)
    elif instr in self.instructionSet['itype']:
        return self.createITypeInstruction(s)
    else:
        raise SyntaxError("Invalid parse instruction")

def main():
    path = 'tests/add_test'

    iparser = Instruction.InstructionParser()
    instrCollection = iparser.parseFile(path)
    simulator = PipelineSimulator.PipelineSimulator(instrCollection)
    simulator.run()

if __name__ == "__main__":
    main()
