from RISCV_Simulator.Instruction import *
import collections


class PipelineSimulator(object):
    operations = {'add': '+', 'addi': '+', 'sub': '-', 'subi': '-',
                  'and': '&', 'andi': '&', 'or': '|', 'ori': '|'}

    # instrCollection object passed in from Instruction parser
    def __init__(self, instrCollection):
        self.instrCount = 0
        self.cycles = 0
        self.__done = False

        # self.pipeline is a list<PipelineStage>
        # with the mapping of:
        #   0 = Fetch
        #   1 = Write Back
        #   2 = Read
        #   3 = Execute
        #   4 = Data Access
        self.pipeline = [
            FetchStage(Nop, self),
            WriteStage(Nop, self),
            ReadStage(Nop, self),
            ExecStage(Nop, self),
            DataStage(Nop, self),
        ]

        # ex: {'x0' : 0, 'x1' : 0 ... 'x2' : 0 }
        self.registers = dict([("x%s" % x, 0) for x in range(32)])

        # set up the main memory construct, a list index starting at 0
        # and continuing to 0xffc
        # goes by every 4 since each one represents a byte
        # this contains all the information about the instruction
        self.mainmemory = dict([(x * 4, 0) for x in range(0xffc4)])

        # programCounter to state where in the instruction collection
        # we are. to find correct spot in mainmemory add 0x100
        self.programCounter = 0x1000

        # the list of instruction objects passed into the simulator,
        # most likely created by parsing text
        self.instrCollection = instrCollection

        # populate main memory with our text of the instructions
        # starting at 0x1000
        y = 0
        for instr in self.instrCollection:
            self.mainmemory[0x1000 + y] = instr
            # each instruction is 4 bytes
            y += 4
    ''' pipeline
    def step(self):
        self.cycles += 1
        # shift the instructions to the next logical place
        # technically we do the Fetch instruction here, which is why
        # FetchStage.advance() does nothing

        # MUST KEEP THIS ORDER
        self.pipeline[1] = WriteStage(self.pipeline[4].instr, self)
        self.pipeline[4] = DataStage(self.pipeline[3].instr, self)
        self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
        self.pipeline[2] = ReadStage(self.pipeline[0].instr, self)
        self.pipeline[0] = FetchStage(None, self)

        # call advance on each instruction in the pipeline
        for pi in self.pipeline:
            pi.advance()
        self.checkDone()
    '''
    def checkDone(self):
        """ Check if we are done and set __done variable """
        # checks if the instructions in the pipeline are nop are not
        # if all nop then we are done
        self.__done = True
        for pi in self.pipeline:
            if pi.instr is not Nop:
                self.__done = False

    def single_cycle(self):
        self.load_next_instruction()
        self.debug()

        self.pipeline[2] = ReadStage(self.pipeline[0].instr, self)
        self.pipeline[2].advance()
        self.pipeline[0] = FetchStage(None, self)
        self.debug()

        self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
        self.pipeline[3].advance()
        self.pipeline[2] = ReadStage(None, self)
        self.debug()

        self.pipeline[4] = DataStage(self.pipeline[3].instr, self)
        self.pipeline[4].advance()
        self.pipeline[3] = ExecStage(None, self)
        self.debug()

        self.pipeline[1] = WriteStage(self.pipeline[4].instr, self)
        self.pipeline[1].advance()
        self.pipeline[4] = DataStage(None, self)
        self.debug()

    def load_next_instruction(self):
        self.__done = False
        self.pipeline[1] = DataStage(None, self)
        self.pipeline[0].advance()
        if self.pipeline[0].instr is Nop:
            self.__done = True

    def run(self):
        """ Run the simulator, call step until we are done """

        while not self.__done:
            self.single_cycle()

        """
        while not self.__done:
            self.step()
            self.debug()
            """

    """ DEBUGGING INFORMATION PRINTING """

    def debug(self):
        print("######################## debug ###########################")
        # self.printStageCollection()
        self.printRegFile()
        print("\n<ProgramCounter>", self.programCounter)
        self.printPipeline()
        # print("<CPI> : ", float(self.cycles) / float(self.instrCount))

    def printPipeline(self):
        print("\n<Pipeline>")
        print(repr(self.pipeline[0]))
        print(repr(self.pipeline[2]))
        print(repr(self.pipeline[3]))
        print(repr(self.pipeline[4]))
        print(repr(self.pipeline[1]))

    def printRegFile(self):
        # """
        print("\n<Register File>")
        for k, v in sorted(self.registers.items()):
            if len(k) != 3:
                print(k, " : ", v, )
            else:
                print("\n", k, " : ", v, )

    '''
    def printStageCollection(self):
        print("<Instruction Collection>")
        for index, item in sorted(self.mainmemory.iteritems()):
            if item != 0:
                print(index, ": ", str(item))
    '''


class PipelineStage(object):
    def __init__(self, instruction, simulator):
        self.instr = instruction
        self.simulator = simulator

    def advance(self):
        pass

    def __repr__(self):
        return str(self) + ':\t' + str(self.instr)


class FetchStage(PipelineStage):
    def advance(self):
        """
        Fetch the next instruction according to simulator program counter
        """
        # if the current program counter is still smaller than the last instruction
        if self.simulator.programCounter < (len(self.simulator.instrCollection) * 4 + 0x1000):
            # increment the instruction counter
            self.simulator.instrCount += 1
            # get another instruction
            self.instr = self.simulator.mainmemory[self.simulator.programCounter]
        else:
            self.instr = Nop
        # increment program counter to the next byte
        self.simulator.programCounter += 4

    def __str__(self):
        return 'Fetch Stage\t'


class ReadStage(PipelineStage):
    def advance(self):
        """
        Read the necessary registers from the registers file
        used in this instruction
        """
        if (self.instr.regRead):
            self.instr.source1RegValue = self.simulator.registers[self.instr.s1]
            if self.instr.immed:
                # check to see if it is a hex value
                if "x0" in self.instr.immed:
                    self.instr.source2RegValue = int(self.instr.immed, 16)
                else:
                    self.instr.source2RegValue = int(self.instr.immed)
            elif self.instr.s2:
                self.instr.source2RegValue = self.simulator.registers[self.instr.s2]

    def __str__(self):
        return 'Read from Register'


class ExecStage(PipelineStage):
    def advance(self):
        """
        Execute the instruction according to its mapping of
        assembly operation to Python operation
        """
        # evalute instruction (assuming its an arithmetic operation)
        print(self.instr.source1RegValue)
        if self.instr is not Nop:
            self.instr.result = eval(
                "%d %s %d" % (
                    self.instr.source1RegValue, self.simulator.operations[self.instr.op], self.instr.source2RegValue))

    def __str__(self):
        return 'Execute Stage\t'


class DataStage(PipelineStage):
    def advance(self):
        """
        If we have to write to main memory, write it first
        and then read from main memory second
        """
        # skip for now since only doing r-type
        pass

    def __str__(self):
        return 'Main Memory'


class WriteStage(PipelineStage):
    def advance(self):
        """
        Write to the register file
        """
        if self.instr.regWrite:
            if self.instr.dest != 'x0':
                self.simulator.registers[self.instr.dest] = self.instr.result

    def __str__(self):
        return 'Write to Register'
