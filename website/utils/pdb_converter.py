from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class ConversionOptions:
    remove_o2_prime: bool = True
    h5_to_c7: bool = True


# RNA residue -> DNA residue mapping used in many PDB conventions
_RNA_TO_DNA: Dict[str, str] = {
    "A": "DA",
    "C": "DC",
    "G": "DG",
    "U": "DT",
    # sometimes RNA uses these 3-letter forms
    "ADE": "DA",
    "CYT": "DC",
    "GUA": "DG",
    "URA": "DT",
}


def convert_pdb_text_to_dna(pdb_text: str, options: ConversionOptions = ConversionOptions()) -> Tuple[str, Dict[str, int]]:
    """Convert RNA residues in PDB text to DNA.

    Returns:
        (converted_text, stats)
    """
    stats = {
        "lines_in": 0,
        "lines_out": 0,
        "atoms_converted": 0,
        "residues_converted": 0,
        "o2prime_removed": 0,
        "h5_renamed": 0,
    }

    seen_residue_keys = set()
    out_lines: List[str] = []

    for line in pdb_text.splitlines(True):
        stats["lines_in"] += 1

        if line.startswith("ATOM"):
            # residue name columns 18-20 (0-based 17:20)
            residue_name = line[17:20].strip()
            mapped = _RNA_TO_DNA.get(residue_name)
            if mapped:
                line = line[:17] + f" {mapped} " + line[21:]
                stats["atoms_converted"] += 1

                # count unique residue conversions (chain + resseq + icode + residue name)
                chain_id = line[21:22]
                res_seq = line[22:26]
                i_code = line[26:27]
                residue_key = (chain_id, res_seq, i_code)
                if residue_key not in seen_residue_keys:
                    seen_residue_keys.add(residue_key)
                    stats["residues_converted"] += 1

            atom_name = line[12:16].strip()

            if options.remove_o2_prime and atom_name == "O2'":
                stats["o2prime_removed"] += 1
                continue

            if options.h5_to_c7 and atom_name == "H5":
                line = line[:12] + " C7 " + line[16:]
                stats["h5_renamed"] += 1

        out_lines.append(line)

    stats["lines_out"] = len(out_lines)
    return "".join(out_lines), stats
