command! -nargs=1 -complete=file LalInitProject call LalInitProject(<q-args>)
command! -nargs=0 LalInitAuto call LalInitAuto()
command! -nargs=0 LalLocate call LalLocate()
command! -nargs=0 LalIsDispatching call LalIsDispatching()
