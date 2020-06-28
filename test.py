import RISCV_Simulator.Instruction as Instruction
import RISCV_Simulator.PipelineSimulator as PipelineSimulator
import os
import sys

def main():
    path = 'tests/add_test'

    iparser = Instruction.InstructionParser()
    instrCollection = iparser.parseFile(path)
    simulator = PipelineSimulator.PipelineSimulator(instrCollection)
    simulator.run()



if __name__ == "__main__":
    main()
