
#include <gba_console.h>
#include <gba_video.h>
#include <gba_interrupt.h>
#include <gba_systemcalls.h>
#include <gba_input.h>
#include <gba_sound.h>
#include <stdio.h>
#include <stdlib.h>

#define RCNT (*(volatile uint16_t *)(0x04000134))
#define SIOCNT (*(volatile uint16_t *)(0x04000128))
#define SIODATA32 (*(volatile uint32_t *)(0x04000120))

#define GAMEPAK_ROM ((volatile uint32_t *)(0x08000000))
enum
{
	MODE_DUMP_ROM = 1,
	MODE_DUMP_SAVE = 2,
	MODE_DUMP_BIOS = 3,
};

uint32_t getGameSize()
{
	int32_t i;
	for (i = (1 << 15); i < (1 << 30); i <<= 1)
	{
		volatile uint16_t *rom = (volatile uint16_t *)(0x08000000 + i);

		bool isEnd = true;
		for (int32_t j = 0; j < 0x1000; j++)
		{
			if (rom[j] != j)
			{
				isEnd = false;
				break;
			}
		}

		if (isEnd)
			break;
	}

	return i;
}

uint32_t exchange32(uint32_t data)
{
	// set data
	SIODATA32 = data;

	// start bit set 0
	SIOCNT &= ~(1 << 7);

	// SO set 0
	SIOCNT &= ~(1 << 3);

	// start bit to 1
	SIOCNT |= (1 << 7);

	// SO set 1 or 0
	if (data & 1)
	{
		SIOCNT |= (1 << 3);
	}
	else
	{
		SIOCNT &= ~(1 << 3);
	}

	// wait start bit 0
	while ((SIOCNT & (1 << 7)))
		;

	return SIODATA32;
}

//---------------------------------------------------------------------------------
// Program entry point
//---------------------------------------------------------------------------------
int main(void)
{
	//---------------------------------------------------------------------------------
	// the vblank interrupt must be enabled for VBlankIntrWait() to work
	// since the default dispatcher handles the bios flags no vblank handler
	// is required
	irqInit();
	irqEnable(IRQ_VBLANK);

	consoleDemoInit();

	// ansi escape sequence to set print co-ordinates
	// /x1b[line;columnH
	iprintf("GBA Sender\nby nikachu2012\n");

	iprintf("Waiting connection...\n");

	// reset RCNT
	RCNT = 0;

	// set use external clock
	SIOCNT &= ~1;

	// use 32 bit mode
	SIOCNT |= (1 << 12);

	uint32_t mode = exchange32(0x10101010);

	// uint32_t start_pos = 0;
	// uint32_t end_pos = 0;
	u32 prevIrqMask = REG_IME;
	REG_IME = 0;
	switch (mode)
	{
	case MODE_DUMP_ROM:
		uint32_t gamesize = getGameSize();

		iprintf("Gamesize: %ldKiB\n", gamesize / 1024);

		uint32_t r = exchange32(gamesize);

		if (r != 0xffffffff){
			iprintf("Assertion Failed!\n");
			break;
		}

		for (size_t i = 0; i < gamesize / 4; i++)
		{
			uint32_t t = exchange32(GAMEPAK_ROM[i]);

			if (t != i)
			{
				iprintf("Sending Assertion Failed!\n");
				break;
			}
		}
		iprintf("Send completed!\n");
		break;
	case MODE_DUMP_SAVE:
		break;
	case MODE_DUMP_BIOS:
		// send data
		for (size_t i = 0; i < 0x4000; i += 4)
		{
			u32 a = (MidiKey2Freq((WaveData *)(i - 4), 180 - 12, 0) * 2) >> 24;
			u32 b = (MidiKey2Freq((WaveData *)(i - 3), 180 - 12, 0) * 2) >> 24;
			u32 c = (MidiKey2Freq((WaveData *)(i - 2), 180 - 12, 0) * 2) >> 24;
			u32 d = (MidiKey2Freq((WaveData *)(i - 1), 180 - 12, 0) * 2) >> 24;

			uint32_t t = exchange32(((a << 24) | (d << 16) | (c << 8) | b));

			if (t != i)
			{
				iprintf("Sending Assertion Failed!\n");
				break;
			}
		}
		iprintf("Send Completed!\n");
		break;
	default:
		iprintf("Undefined mode.\n");
		break;
	}
	REG_IME = prevIrqMask;

	while (1)
	{
		Halt();
	}
}
