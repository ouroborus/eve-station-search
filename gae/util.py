_maxint = 2147483647 # don't have to load sys

def trim(docstring):
  """
  http://codedump.tumblr.com/post/94712647/handling-python-docstring-indentation
  
  Clean up docstrings. 
  """
  if not docstring:
    return ''
  lines = docstring.expandtabs().splitlines()
  
  # Determine minimum indentation (first line doesn't count):
  indent = _maxint
  for line in lines[1:]:
    stripped = line.lstrip()
    if stripped:
      indent = min(indent, len(line) - len(stripped))
  
  # Remove indentation (first line is special):
  trimmed = [lines[0].strip()]
  if indent < _maxint:
    for line in lines[1:]:
      trimmed.append(line[indent:].rstrip())
  
  # Strip off trailing and leading blank lines:
  while trimmed and not trimmed[-1]:
    trimmed.pop()
  while trimmed and not trimmed[0]:
    trimmed.pop(0)
  return '\n'.join(trimmed)
