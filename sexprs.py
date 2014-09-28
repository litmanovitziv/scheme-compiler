
import reader as p

def foo(s,a):
	
	if s:
		return Pair(s[0],foo(s[1:],a))
	else:
		return a

class AbstractSexpr:
	@staticmethod
	def readFromString(str):
		return p.pSexpr.match(str)

	def accept(self, visitor):
		pass

class AbstractSexprVisitor:
	def visit(self, expr):
		pass
	def visitVoid(self):
		pass
	def VisitNil(self):
		pass
	def visitBoolean(self):
		pass
	def visitChar(self):
		pass
	def visitInteger(self):
		pass
	def visitHexNumber(self):
		pass
	def visitFraction(self):
		pass
	def visitString(self):
		pass
	def visitSymbol(self):
		pass
	def visitPair(self):
		pass
	def visitVector(self):
		pass

class SexprGetClassVisitor(AbstractSexprVisitor):
	def visit(self, expr):
		return expr.accept(self)
	def visitVoid(self):
		return 'Void'
	def VisitNil(self):
		return 'Nil'
	def visitBoolean(self):
		return 'Boolean'
	def visitChar(self):
		return 'Char'
	def visitInteger(self):
		return 'Integer'
	def visitHexNumber(self):
		return 'HexNumber'
	def visitFraction(self):
		return 'Fraction'
	def visitString(self):
		return 'String'
	def visitSymbol(self):
		return 'Symbol'
	def visitPair(self):
		return 'Pair'
	def visitVector(self):
		return 'Vector'

def getClass(c):
	v = SexprGetClassVisitor()
	return v.visit(c)

class Void(AbstractSexpr):   
	def __init__(self):
		pass
	def __str__(self):
		return ''

	def accept(self, visitor):
		return visitor.visitVoid()

class Nil(AbstractSexpr): 
	def __init__(self):
		pass

	def __str__(self):
		return '()'

	def accept(self, visitor):
		return visitor.VisitNil()

class Boolean(AbstractSexpr): 
	def __init__(self, pred):
		self.pred = pred

	def __str__(self):
		ans = '#'
		if self.pred == True:
			ans = ans+'t'
		else:
			ans = ans + 'f'
		return ans

	def getValue(self):
		return self.pred

	def accept(self, visitor):
		return visitor.visitBoolean()

# XXX
class Char(AbstractSexpr): 
	def __init__(self, ch, name = None):
		self.ch = ch
		self.name = name

	def __str__(self):
		if self.name:
			return '#\\' + self.name
		else:
			return chr(self.ch)

	def accept(self, visitor):
		return visitor.visitChar()

	def getValue(self):
		return self.ch

class AbstractNumber(AbstractSexpr):
	pass

# XXX
class Integer(AbstractNumber):
	def __init__(self, num):
		self.num = int(num)
		
	def __str__(self):
		return str(self.num)

	def accept(self, visitor):
		return visitor.visitInteger()

	def getValue(self):
		return self.num

	def sign(self,s):
		if s=='-':
			self.num = -self.num
		else:
			pass
		return self

# XXX
class HexNumber(AbstractNumber):
	def __init__(self, num):
		self.num = int(num,16)
		self.st = num

	def __str__(self):
		return str('0x'+self.st) 

	def accept(self, visitor):
		return visitor.visitHexNumber()

	def getValue(self):
		return self.num

	def sign(self,s):
		print(self.num)
		if s=='-':
			self.num = -self.num
		else:
			pass

		print(self.num)
		return self

class Fraction(AbstractNumber):
	def __init__(self, numerator, denumerator):
		self.numerator = numerator
		self.denumerator = denumerator
		
	def __str__(self):
		return str(self.numerator) + '/' +str(self.denumerator)

	def accept(self, visitor):
		return visitor.visitFraction()

	def sign(self,s):
		if s=='-':
			self.numerator = -self.numerator
		else:
			pass
		return self

class String(AbstractSexpr):
	def __init__(self, s):
		self.s = s[1:-1]

	def __str__(self):
		return "\"" + repr(self.s)[1:-1] + "\""

	def accept(self, visitor):
		return visitor.visitString()

class Symbol(AbstractSexpr):
	def __init__(self, s):
		self.s = s

	def __str__(self):
		return str(self.s)
#XXX
	def __eq__(self, other):
		return other.s == self.s

	def accept(self, visitor):
		return visitor.visitSymbol()

class Pair(AbstractSexpr):
	def __init__(self, car, cdr):
		self.car = car
		self.cdr = cdr

	def __str__(self):
		s = str(self.car)
		temp = self.cdr
		while getClass(temp)!='Nil':
			try:
				s = s + ' ' + str(temp.car)
				temp = temp.cdr
			except:
				s =  s + ' . ' + str(temp)
				break
		return '(' + s + ')'

	def isProperList(self):
		if getClass(self.cdr)=='Nil':
			return True
		else:
			try:
				return self.cdr.isProperList()
			except Exception:
				return False

	def accept(self, visitor):
		return visitor.visitPair()

	def getLength(self):
		if getClass(self.cdr)=='Nil':
			return 1
		else:
			return 1 + self.cdr.getLength()

class Vector(AbstractSexpr):
	def __init__(self, car, cdr):
		self.car = car
		self.cdr = cdr

	def __str__(self):
		s = str(self.car)
		temp = self.cdr
		while getClass(temp)!='Nil':
			try:
				s = s + ' ' + str(temp.car)
				temp = temp.cdr
			except:
				s =  s + ' . ' + str(temp)
				break
		return '#(' + s + ')'

	def getLength(self):
		return 1 + self.cdr.getLength()

	def accept(self, visitor):
		return visitor.visitVector()

