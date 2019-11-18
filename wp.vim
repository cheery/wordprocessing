" This trick uses concealing in vim editor
" to represent few control characters for formatting.
set conceallevel=1
set concealcursor=ni

call matchadd('Conceal',nr2char(0x10),10,-1,{'conceal': '('})
call matchadd('Conceal',nr2char(0x11),10,-1,{'conceal': ')'})
call matchadd('Conceal',nr2char(0x12),10,-1,{'conceal': '['})
call matchadd('Conceal',nr2char(0x13),10,-1,{'conceal': ']'})
call matchadd('Conceal',nr2char(0x14),10,-1,{'conceal': '<'})
call matchadd('Conceal',nr2char(0x15),10,-1,{'conceal': '>'})
call matchadd('Conceal',nr2char(0x16),10,-1,{'conceal': ':'})

hi! link Conceal Special

"TODO: Fix
"inoremap <C-Space>; <C-v><C-a>
"inoremap <C-Space>c <C-v><C-a>
"inoremap <C-Space>~ <C-v><C-b>
"inoremap <C-Space>t <C-v><C-b>
"inoremap <C-Space>\| <C-v><C-c>
"inoremap <C-Space><Tab> <C-v><C-c>
"inoremap <C-Space>[ <C-v><C-b>
"inoremap <C-Space>] <C-v><C-f>
"inoremap <C-Space>( <C-v><C-q>
"inoremap <C-Space>) <C-v><C-r>
"inoremap <C-Space>: <C-v><C-v>
"inoremap <C-Space><Space> <C-v><C-v>
