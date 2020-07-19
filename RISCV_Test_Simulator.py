path = 'tests/add_test'
funct7_and_funct3_decode = {
    '0000000000': 'add',
    '0100000000': 'sub',
    '0000000111': 'and',
    '0000000110': 'or',
    '0000000100': 'xor',
}

itype_funct3_decode = {
    '000': 'addi',
    '100': 'xori',
    '110': 'or',
    '111': 'andi',
}

opcode_decode = {
    '0110011': 'R-type',
    '0010011': 'I-type',
}

class RTypeInstruction:
    def __init__(self, s):
        self.result = None

        self.source1RegValue = None
        self.source2RegValue = None

        #fields
        self.funct7 = None
        self.rs2 = None
        self.rs1 = None
        self.funct3 = None
        self.rd = None
        self.opcode = None

        self.funct7_mapping = {
            'add': '0000000',
            'and': '0000000',
            'or': '0000000',
            'xor': '0000000',
            'sll': '0000000',
            'slt': '0000000',
            'sub': '0100000'
        }
        self.funct3_mapping = {
            'add': '000',
            'sub': '000',
            'sll': '001',
            'slt': '010',
            'xor': '100',
            'or': '110',
            'and': '111'
        }

        self.funct7 = self.funct7_mapping[s[0]]
        self.funct3 = self.funct3_mapping[s[0]]
        self.opcode = '0110011'

        # converts to binary of fixed length 5
        self.rd = bin(int(s[1][1:])).replace("0b", "").zfill(5)
        self.rs1 = bin(int(s[2][1:])).replace("0b", "").zfill(5)
        self.rs2 = bin(int(s[3][1:])).replace("0b", "").zfill(5)

        self.instruction_repr = self.funct7 + self.rs2 + \
               self.rs1 + self.funct3 + \
               self.rd + self.opcode

    def __repr__(self):
        return self.instruction_repr

class ITypeInstruction:
    def __init__(self, s):
        self.result = None

        self.source1RegValue = None
        self.source2RegValue = None

        #fields
        self.imm = None
        self.rs1 = None
        self.funct3 = None
        self.rd = None
        self.opcode = None


        self.funct3_mapping = {
            'addi': '000',
            'slti': '',
            'sltiu': '',
            'xori':  '100',
            'or': '110',
            'andi': '111',

        }

        self.funct3 = self.funct3_mapping[s[0]]
        self.opcode = '0010011'

        # converts to binary of fixed length 5
        self.rd = bin(int(s[1][1:])).replace("0b", "").zfill(5)
        self.rs1 = bin(int(s[2][1:])).replace("0b", "").zfill(5)

        self.imm = bin(int(s[3])).replace("0b", "").zfill(12)
        self.instruction_repr = self.imm + self.rs1 + self.funct3 + self.rd + self.opcode

    def __repr__(self):
        return self.instruction_repr

class Nop():
    pass


class InstructionParser(object):
    def __init__(self):
        self.instructionSet = {
            'rtype': ['add', 'sub', 'and', 'or', 'jr', 'nor', 'slt', 'xor'],
            'itype': ['addi', 'ori', 'andi', 'xori', 'bne', 'beq', 'lw', 'sw'],
        }

    def parse(self, s):
        # splits strings into tokens
        s = s.split()
        # get instruction type from first element
        instr = s[0]

        # if rtype then make into a rtype instruction
        if instr in self.instructionSet['rtype']:
            return RTypeInstruction(s)
        elif instr in self.instructionSet['itype']:
            return ITypeInstruction(s)
        else:
            raise SyntaxError("Invalid parse instruction")

    def parseFile(self, filename):
        # parses file to recieve instructions
        with open(filename) as f:
            data = filter((lambda x: x != '\n'), f.readlines())
        return [self.parse(a.replace(',', ' ')) for a in data]

    def output_binary(self, instrCollection):
        filename = 'bin_dump'
        with open(filename, 'w') as f:
            for instr in instrCollection:
                f.write(("%s\n" % instr))

class PipelineSimulator(object):
    operations = {'add': '+', 'addi': '+', 'sub': '-', 'subi': '-',
                  'and': '&', 'andi': '&', 'or': '|', 'ori': '|',
                  'xor': '^', 'xori': '^'}

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
            FetchStage(None, self),
            WriteStage(None, self),
            ReadStage(None, self),
            ExecStage(None, self),
            DataStage(None, self),
        ]

        # ex: {'x0' : 0, 'x1' : 0 ... 'x2' : 0 }
        self.registers = dict([(x, ["x%s" % x, 0]) for x in range(32)])

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
            self.mainmemory[0x1000 + y] = instr.instruction_repr
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
    def dump(self, instrCollection):
        filename = 'bin_dump'
        with open(filename, 'w') as f:
            for location, instr in self.mainmemory:
                f.write(("%d: %s\n" % location, instr))

    def checkDone(self):
        """ Check if we are done and set __done variable """
        # checks if the instructions in the pipeline are nop are not
        # if all nop then we are done
        self.__done = True
        for pi in self.pipeline:
            if pi.instr is not None:
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
        if self.pipeline[0].instr is None:
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
        for k, v in self.registers.items():
            print(v[0], v[1])
            '''
            if len(k) != 3:
                print(k, " : ", v, )
            else:
                print("\n", k, " : ", v, )
            '''

    '''
    def printStageCollection(self):
        print("<Instruction Collection>")
        for index, item in sorted(self.mainmemory.iteritems()):
            if item != 0:
                print(index, ": ", str(item))
    '''

class PipelineInstruction():
    def __init__(self, instr_representation):
        self.binary = instr_representation
        self.result = None
        self.operation = None
        self.source1RegValue = None
        self.source2RegValue = None
        self.dest = None

        #fields
        self.imm = None
        self.funct7 = None
        self.rs2 = None
        self.rs1 = None
        self.funct3 = None
        self.rd = None
        self.opcode = None
    def __repr__(self):
        return self.binary

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
            self.instr = PipelineInstruction(self.simulator.mainmemory[self.simulator.programCounter])
        else:
            self.instr = None
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
        if self.instr is not None:
            self.instr.opcode = self.instr.binary[25:]
            if opcode_decode[self.instr.opcode] == 'R-type':
                self.decode_rtype()
            elif opcode_decode[self.instr.opcode] == 'I-type':
                self.decode_itype()
            else:
                raise SyntaxError("Invalid opcode")

    def decode_rtype(self):
        self.instr.funct3 = self.instr.binary[17:20]
        self.instr.funct7 = self.instr.binary[0:7]
        funct7_and_funct3 = self.instr.funct7 + self.instr.funct3
        if funct7_and_funct3_decode[funct7_and_funct3] == 'add':
            self.instr.operation = 'add'
        elif funct7_and_funct3_decode[funct7_and_funct3] == 'sub':
            self.instr.operation = 'sub'
        elif funct7_and_funct3_decode[funct7_and_funct3] == 'and':
            self.instr.operation = 'and'
        elif funct7_and_funct3_decode[funct7_and_funct3] == 'or':
            self.instr.operation = 'or'
        elif funct7_and_funct3_decode[funct7_and_funct3] == 'xor':
            self.instr.operation = 'xor'
        self.instr.source1RegValue = self.simulator.registers[int(self.instr.binary[12:17], 2)][1]
        self.instr.source2RegValue = self.simulator.registers[int(self.instr.binary[7:12], 2)][1]

    def decode_itype(self):
        self.instr.imm = self.instr.binary[0:12]
        self.instr.rs1 = self.instr.binary[12:17]
        self.instr.funct3 = self.instr.binary[17:20]
        if itype_funct3_decode[self.instr.funct3] == 'addi':
            self.instr.operation = 'addi'
        elif itype_funct3_decode[self.instr.funct3] == 'andi':
            self.instr.operation = 'andi'
        elif itype_funct3_decode[self.instr.funct3] == 'ori':
            self.instr.operation = 'ori'
        elif itype_funct3_decode[self.instr.funct3] == 'xori':
            self.instr.operation = 'xori'
        self.instr.source1RegValue = self.simulator.registers[int(self.instr.rs1, 2)][1]
        self.instr.source2RegValue = int(self.instr.imm, 2)


    def __str__(self):
        return 'Read from Register'


class ExecStage(PipelineStage):
    def advance(self):
        """
        Execute the instruction according to its mapping of
        assembly operation to Python operation
        """

        if self.instr is not None:
            self.instr.result = eval(
                "%d %s %d" % (
                    self.instr.source1RegValue, self.simulator.operations[self.instr.operation], self.instr.source2RegValue))
            print(self.instr.result)

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
        if self.instr is not None:
            self.simulator.registers[int(self.instr.binary[20:25], 2)][1] = self.instr.result

    def __str__(self):
        return 'Write to Register'


if __name__ == "__main__":
    path = 'tests/add_test'

    iparser = InstructionParser()
    instrCollection = iparser.parseFile(path)
    iparser.output_binary(instrCollection)
    simulator = PipelineSimulator(instrCollection)
    simulator.run()
