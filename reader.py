#!/usr/bin/python
# -*- coding: utf-8 -*-

import pc
import sexprs as classes

ps = pc.ParserStack()

def makePair(car,cdr):
    if car:
        return classes.Pair(car[0],makePair(car[1:],cdr))
    else:
        return cdr

def makeVector(bla):
    return classes.Vector(bla.car,bla.cdr)

whiteSpace = ps.const(lambda s : s <= ' ')\
               .star()\
               .done()


singleWhiteSpace = ps.const(lambda s : s <= ' ')\
               .done()

SexprComment = ps.word('#;')\
                 .done()

EOL = ps.const(lambda ch : ch =='\n')\
        .const(lambda ch : ch =='\r')\
        .const(lambda ch : ch == '\r\n')\
        .disjs(3)\
        .done()

lineComment =  ps.parser(pc.pcWord(';'))\
                 .const(lambda ch: ch !='\n' and ch !='\r' and ch !='\r\n')\
                 .star()\
                 .parser(EOL)\
                 .catens(3)\
                 .done()
                       
boolean = ps.word('#')\
            .const(lambda ch : ch == 't' or ch == 'T' or ch == 'f' or ch == 'F')\
            .caten()\
            .pack(lambda s: classes.Boolean(s[1]=='t'))\
            .done()

natNum = ps.const(lambda ch : '0'<= ch <='9' )\
            .plus()\
            .pack(lambda s: classes.Integer("".join(s)))\
            .done()

             
pHexDigit = ps.const(lambda ch: 'a'<= ch <='f' or 'A'<= ch <='F' )\
              .const(lambda ch : '0'<= ch <='9' )\
              .disj()\
              .pack(lambda s : s if ('a' <= s <= 'f' or '0' <= s <= '9') else chr(ord(s)+32))\
              .done()

             
hexNum = ps.word('0')\
           .const(lambda ch: ch =='x' or ch =='X' or ch =='h' or ch =='H')\
           .parser(pHexDigit)\
           .plus()\
           .catens(3)\
           .pack(lambda s : classes.HexNumber("".join(s[2])))\
           .done()
               
pUnsigned = ps.parser(hexNum)\
            .parser(natNum)\
            .disj()\
            .done()

pSigned = ps.parser(pc.pcWord('+'))\
            .parser(pc.pcWord('-'))\
            .disj()\
            .parser(pUnsigned)\
            .caten()\
            .pack(lambda s: s[1].sign(s[0][0]))\
            .done()


frac = ps.parser(pSigned)\
         .parser(pUnsigned)\
         .disj()\
         .parser(pc.pcWord('/'))\
         .parser(pUnsigned)\
         .catens(3)\
         .pack(lambda s : classes.Fraction(s[0],s[2]))\
         .done()
         
        
pNum = ps.parser(frac)\
        .parser(pSigned)\
        .parser(pUnsigned)\
        .disjs(3)\
        .done()

pLetter = ps.const(lambda ch: 'a'<= ch <='z')\
            .pack(lambda s: chr(ord(s)-32))\
            .const(lambda ch:'A'<= ch <='Z' )\
            .disj()\
            .done()

symbol = ps.parser(pc.const(lambda ch : '<' <= ch <= '?' or ch == '$' or ch == '!'\
                            or ('*' <= ch <= '/' and ch != ',' and ch != '.')\
                            or  '^' <= ch <= '_'))\
           .const(lambda ch : '0'<= ch <='9' )\
           .parser(pLetter)\
           .disjs(3)\
           .plus()\
           .pack(lambda s : classes.Symbol("".join(s)))\
           .done()

pString = ps.word('\"')\
                 .const(lambda ch: ch!='\"')\
                 .star()\
                 .word('\"')\
                 .caten()\
                 .pack(lambda s: "".join(s[0]+s[1]))\
                 .star()\
                 .caten()\
                 .pack(lambda s: (classes.String(s[0][0]+"".join(s[1]))) )\
                 .done()

pNamedChar = ps.wordCI('newline')\
                .wordCI('return')\
                .wordCI('tab')\
                .wordCI('page')\
                .wordCI('lambda')\
                .disjs(5)\
                .pack(lambda s: classes.Char({'newline':10,'return':13,'tab':9,'page':12,'lambda':955}["".join(s)], name = "".join(s)))\
                .done()

pByte = ps.parser(pHexDigit)\
          .parser(pHexDigit)\
          .caten()\
          .pack(lambda s: int(s[0],16)*16+int(s[1],16))\
          .done()

pWord = ps.parser(pByte)\
          .parser(pByte)\
          .caten()\
          .pack(lambda s: s[0]*16*16+s[1])\
          .done()

pHexChar = ps.const(lambda c: c=='x')\
            .parser(pWord)\
            .parser(pByte)\
            .disj()\
            .caten()\
            .pack(lambda s: classes.Char(s[1]))\
            .done()

pVisibleChar = ps.const(lambda c: c>' ')\
                .pack(lambda s: classes.Char(ord(s)))\
                .done()

pChar =  ps.word('#\\')\
          .parser(pNamedChar)\
          .parser(pHexChar)\
          .parser(pVisibleChar)\
          .disjs(3)\
          .caten()\
          .pack(lambda s: s[1])\
          .done()


pNil = ps.word('(')\
        .parser(singleWhiteSpace)\
        .parser(SexprComment)\
        .disj()\
        .star()\
        .word(')')\
        .catens(3)\
        .pack(lambda s: classes.Nil())\
        .done()

properList = ps.parser(pc.pcWord('('))\
               .delayed_parser(lambda : pSexpr)\
               .plus()\
               .parser(pc.pcWord(')'))\
               .catens(3)\
               .pack(lambda m: makePair(m[1],classes.Nil()) )\
               .done()
         
improperList = ps.parser(pc.pcWord('('))\
                 .delayed_parser(lambda : pSexpr)\
                 .plus()\
                 .parser(pc.pcWord('.'))\
                 .pack(lambda c : c[0])\
                 .delayed_parser(lambda : pSexpr)\
                 .parser(pc.pcWord(')'))\
                 .catens(5)\
                 .pack(lambda m: makePair(m[1],m[3]))\
                 .done()
         
pPair = ps.parser(properList)\
         .parser(improperList)\
         .disj()\
         .done()

pVector = ps.word('#(')\
           .delayed_parser(lambda : pSexpr)\
           .plus()\
           .parser(pc.pcWord(')'))\
           .catens(3)\
           .pack(lambda m: makeVector(makePair(m[1],classes.Nil())))\
           .done()

pSkip = ps.parser(singleWhiteSpace)\
          .parser(SexprComment)\
          .disj()\
          .star()\
          .pack(lambda s : '' )\
          .done()

 
pQuoteSign = ps.const(lambda c: c=='\'')\
              .const(lambda c: c=='`')\
              .word(',@')\
              .const(lambda c: c==',')\
              .disjs(4)\
              .pack(lambda s: classes.Symbol({ '`':'quasiquote',\
                                               ',':'unquote',\
                                               '\'':'quote',\
                                               ',@':'unquote-splicing'}["".join(s)]))\
              .done()
pQuoted = ps.parser(pQuoteSign)\
            .delayed_parser(lambda: pSexpr)\
            .caten()\
            .pack(lambda s: classes.Pair(s[0], classes.Pair(s[1],classes.Nil())))\
            .done()

pSexpr = ps.parser(pSkip)\
           .parser(pNum)\
           .parser(boolean)\
           .parser(pPair)\
           .parser(pNil)\
           .parser(pChar)\
           .parser(pVector)\
           .parser(pString)\
           .parser(pQuoted)\
           .parser(symbol)\
           .disjs(9)\
           .parser(pSkip)\
           .catens(3)\
           .pack(lambda s : s[1])\
           .done()
