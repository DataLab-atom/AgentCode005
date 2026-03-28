%% Nature magazine bibliography style
%% Simplified version following Nature's numbered reference format
%% References are numbered in order of appearance

ENTRY
  { author
    title
    journal
    year
    volume
    number
    pages
    doi
    note
    booktitle
    publisher
    address
    edition
    editor
    howpublished
    url
  }
  {}
  { label }

INTEGERS { output.state before.all mid.sentence after.sentence after.block }

FUNCTION {init.state.consts}
{ #0 'before.all :=
  #1 'mid.sentence :=
  #2 'after.sentence :=
  #3 'after.block :=
}

STRINGS { s t }

FUNCTION {output.nonnull}
{ 's :=
  output.state mid.sentence =
    { ", " * write$ }
    { output.state after.block =
        { add.period$ write$
          newline$
          "\newblock " write$
        }
        { output.state before.all =
            'write$
            { add.period$ " " * write$ }
          if$
        }
      if$
      mid.sentence 'output.state :=
    }
  if$
  s
}

FUNCTION {output}
{ duplicate$ empty$
    'pop$
    'output.nonnull
  if$
}

FUNCTION {output.check}
{ 't :=
  duplicate$ empty$
    { pop$ "empty " t * " in " * cite$ * warning$ }
    'output.nonnull
  if$
}

FUNCTION {output.bibitem}
{ newline$
  "\bibitem{" write$
  cite$ write$
  "}" write$
  newline$
  ""
  before.all 'output.state :=
}

FUNCTION {fin.entry}
{ add.period$
  write$
  newline$
}

FUNCTION {new.block}
{ output.state before.all =
    'skip$
    { after.block 'output.state := }
  if$
}

FUNCTION {not}
{   { #0 }
    { #1 }
  if$
}

FUNCTION {and}
{   'skip$
    { pop$ #0 }
  if$
}

FUNCTION {or}
{   { pop$ #1 }
    'skip$
  if$
}

FUNCTION {new.sentence}
{ output.state after.block =
    'skip$
    { output.state before.all =
        'skip$
        { after.sentence 'output.state := }
      if$
    }
  if$
}

FUNCTION {format.names}
{ 's :=
  #1 'nameptr :=
  s num.names$ 'numnames :=
  numnames 'namesleft :=
    { namesleft #0 > }
    { s nameptr "{vv~}{ll}{, jj}{, f.}" format.name$ 't :=
      nameptr #1 >
        { namesleft #1 >
            { ", " * t * }
            { " \& " * t * }
          if$
        }
        't
      if$
      nameptr #1 + 'nameptr :=
      namesleft #1 - 'namesleft :=
    }
  while$
}

INTEGERS { nameptr namesleft numnames }

FUNCTION {format.authors}
{ author empty$
    { "" }
    { author format.names }
  if$
}

FUNCTION {format.title}
{ title empty$
    { "" }
    { title }
  if$
}

FUNCTION {format.journal}
{ journal empty$
    { "" }
    { "\textit{" journal * "}" * }
  if$
}

FUNCTION {format.vol.pages}
{ volume empty$
    { "" }
    { "\textbf{" volume * "}" *
      pages empty$
        'skip$
        { ", " * pages * }
      if$
    }
  if$
}

FUNCTION {format.year}
{ year empty$
    { "" }
    { "(" year * ")" * }
  if$
}

FUNCTION {format.doi}
{ doi empty$
    { "" }
    { "" }
  if$
}

FUNCTION {article}
{ output.bibitem
  format.authors "author" output.check
  new.block
  format.title "title" output.check
  new.block
  format.journal output
  format.vol.pages output
  format.year output
  format.doi output
  fin.entry
}

FUNCTION {book}
{ output.bibitem
  format.authors "author" output.check
  new.block
  format.title "title" output.check
  new.block
  publisher output
  format.year output
  fin.entry
}

FUNCTION {default.type} { article }

READ

FUNCTION {sortify}
{ purify$
  "l" change.case$
}

INTEGERS { len }

INTEGERS { last.extra.num }

FUNCTION {forward.pass}
{ last.extra.num #0 :=
}

FUNCTION {begin.bib}
{ preamble$ empty$
    'skip$
    { preamble$ write$ newline$ }
  if$
  "\begin{thebibliography}{99}" write$ newline$
}

FUNCTION {end.bib}
{ newline$
  "\end{thebibliography}" write$ newline$
}

EXECUTE {begin.bib}

ITERATE {call.type$}

EXECUTE {end.bib}
