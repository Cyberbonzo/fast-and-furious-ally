ENTRY(projection)
SECTIONS {
 . = 0x3652000;
 .text : { *(.text*) }
 .rodata : { *(.rodata*) }
 .data : { *(.data*) }
 .bss : { *(.bss*) *(COMMON) }
 _end = .;
 /DISCARD/ : { *(.comment*) *(.note*) *(.eh_frame*) }
}
