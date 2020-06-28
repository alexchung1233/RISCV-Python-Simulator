from RISCV_Simulator.Instruction import *
import collections


class PipelineSimulator(object):
    operations = {'add': '+', 'addi': '+', 'sub': '-', 'subi': '-',
                  'and': '&', 'andi': '&', 'or': '|', 'ori': '|'}

    # instrCollection object passed in from Instruction parser
    def __init__(self, instrCollection):
        self.instrCount = 0
        self.cycles = 0
        self.hazardList = []
        self.__done = False
        self.branched = False
        self.stall = False

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

        # ex: {'$r0' : 0, '$r1' : 0 ... '$r31' : 0 }
        self.registers = collections.OrderedDict([("$r%s" % x, 0) for x in range(32)])

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


        #set initial value for testing
        self.registers['$r5'] = 5
        self.registers['$r0'] = 5


    def step(self):
        self.cycles += 1
        # shift the instructions to the next logical place
        # technically we do the Fetch instruction here, which is why
        # FetchStage.advance() does nothing

        # MUST KEEP THIS ORDER
        self.pipeline[1] = WriteStage(self.pipeline[4].instr, self)
        if self.stall:
            self.pipeline[4] = DataStage(Nop, self)
            self.stall = False
        else:
            self.pipeline[4] = DataStage(self.pipeline[3].instr, self)
            self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
            self.pipeline[2] = ReadStage(self.pipeline[0].instr, self)
            self.pipeline[0] = FetchStage(None, self)

        # call advance on each instruction in the pipeline
        for pi in self.pipeline:
            pi.advance()
        # now that everything is done, remove the register from
        # the hazard list

        self.checkDone()

        # if we stalled our branched we didn't want to load a new
        # so keep the program counter where it is
        if self.stall or self.branched:
            self.programCounter -= 4
            self.branched = False

    def checkDone(self):
        """ Check if we are done and set __done variable """
        #checks if the instructions in the pipeline are nop are not
        #if all nop then we are done
        self.__done = True
        for pi in self.pipeline:
            if pi.instr is not Nop:
                self.__done = False

    def run(self):
        """ Run the simulator, call step until we are done """
        while not self.__done:
            self.step()
            self.debug()

    ### DEBUGGING INFORMATION PRINTING ###
    def debug(self):
        print("######################## debug ###########################")
        # self.printStageCollection()
        self.printRegFile()
        print("\n<ProgramCounter>", self.programCounter)
        self.printPipeline()
        #print("<CPI> : ", float(self.cycles) / float(self.instrCount))

    def printPipeline(self):
        print("\n<Pipeline>")
        print(repr(self.pipeline[0]))
        print(repr(self.pipeline[2]))
        print(repr(self.pipeline[3]))
        print(repr(self.pipeline[4]))
        print(repr(self.pipeline[1]))


    def printRegFile(self):
        #"""
        print("\n<Register File>")
        for k,v in sorted(self.registers.items()):
            if len(k) != 3:
                print(k, " : " , v,)
            else :
                print("\n",k, " : ", v,)
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
        # increment program counter
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
            #for now two registers no immediate
            if self.instr.s2:
                self.instr.source2RegValue = self.simulator.registers[self.instr.s2]

    def __str__(self):
        return 'Read from Register'


class ExecStage(PipelineStage):
    def advance(self):
        """
        Execute the instruction according to its mapping of
        assembly operation to Python operation
        """
        #evalute instruction (assuming its an arithmetic operation)
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
            if self.instr.dest == '$r0':
                # Edit: don't raise exception just ignore it
                # raise Exception('Cannot assign to register $r0')
                pass
            # writes the result of instruction to the destination register
            elif self.instr.dest:
                self.simulator.registers[self.instr.dest] = self.instr.result

    def __str__(self):
        return 'Write to Register'
