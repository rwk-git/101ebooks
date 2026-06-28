#!/usr/bin/env python3
import base64
import os
import subprocess
import sys
import json
import re
from typing import Callable, Any
from dataclasses import dataclass, field, replace as evolve

@dataclass
class SGF:
  initial_whites: list[str]
  initial_blacks: list[str]
  moves: list[str]

  height: int = field(init=False)
  width: int = field(init=False)

  def __post_init__(self):
    for moves in [self.initial_whites, self.initial_blacks, self.moves]:
      for m in moves:
        assert isinstance(m, str)
        assert(len(m) == 2)
        assert ord('a') <= ord(m[0]), m[0]
        assert ord(m[0]) <= ord('s'), m[0]
    initial_stones = self.initial_blacks + self.initial_whites
    self.height = max((19 - ord(m[1]) + ord('a') for m in initial_stones), default=0)
    self.width = max((1 + ord(m[0]) - ord('a') for m in initial_stones), default=0)

  def __add__(self, other: "SGF") -> "SGF":
    return SGF(
      initial_whites=self.initial_whites + other.initial_whites,
      initial_blacks=self.initial_blacks + other.initial_blacks,
      moves=self.moves + other.moves,
    )

  def map(self, transformation: Callable[[str], str]) -> "SGF":
    return SGF(
      initial_whites=list(map(transformation, self.initial_whites)),
      initial_blacks=list(map(transformation, self.initial_blacks)),
      moves=list(map(transformation, self.moves)),
    )

  def rotate(self) -> "SGF":
    return self.hflip().sflip()

  def hflip(self) -> "SGF":
    return self.map(lambda x: f"{chr(ord('a') + ord('s') - ord(x[0]))}{x[1]}")

  def sflip(self) -> "SGF":
    return self.map(lambda x: f"{x[1]}{x[0]}")

  def to_sgf(self) -> str:
    ab = "".join(f"[{m}]" for m in self.initial_blacks)
    aw = "".join(f"[{m}]" for m in self.initial_whites)
    moves = "".join(
      f";{'B' if i%2==0 else 'W'}[{m}]"
      for i, m in enumerate(self.moves)
    )
    return f"(;\nAB{ab}\nAW{aw}\n{moves})"

  def to_gnos(self, height_cutoff: int = 11) -> str:
    goban = [
        list("<(((((((((((((((((>"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[++*+++++*+++++*++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[++*+++++*+++++*++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[++*+++++*+++++*++]"),
        list(r"[+++++++++++++++++]"),
        list(r"[+++++++++++++++++]"),
        list(r",))))))))))))))))).")
    ]

    to_coord = lambda x: (ord(x[0]) - ord("a"), ord(x[1]) - ord("a"))
    for move in self.initial_blacks:
      col, row = to_coord(move)
      goban[row][col] = "@"
    for move in self.initial_whites:
      col, row = to_coord(move)
      goban[row][col] = "!"

    char91 = lambda c: "\\char91" if c == "[" else c
    result = "{\\gnos%\n"
    height_cutoff = 19 if self.height > height_cutoff else height_cutoff
    goban = goban[-height_cutoff:]
    for row in goban:
      row_str = "".join(map(char91, row))
      result += "\\line{" + row_str + "}\n"
    result += "}%"

    return result

  @staticmethod
  def from_base64(b64: str, black_first: bool) -> "SGF":
    for key in ["101222", "101333"]:
      n = base64.b64decode(b64).decode("utf-8")
      r = 0
      i = []
      for o in range(len(n)):
          i.append(chr(ord(n[o]) ^ ord(key[r])))
          r = (r + 1) % len(key)
      try:
        match eval("".join(i)):
          case [bs, ws] if black_first:
            return SGF(initial_whites=ws, initial_blacks=bs, moves=[])
          case [ws, bs]:
            return SGF(initial_whites=ws, initial_blacks=bs, moves=[])
          case _:
            assert(False)
      except Exception:
        continue
    raise ValueError()

  @staticmethod
  def from_sgf(input: str) -> "SGF":
    ab_pattern = r"AB(\[[a-z]{2}\])+"
    aw_pattern = r"AW(\[[a-z]{2}\])+"
    moves_pattern = r";[BW]\[([a-z]{2})\]"

    ab_match = re.search(ab_pattern, input)
    aw_match = re.search(aw_pattern, input)
    ab_list = re.findall(r"\[([a-z]{2})\]", ab_match.group(0)) if ab_match else []
    aw_list = re.findall(r"\[([a-z]{2})\]", aw_match.group(0)) if aw_match else []
    moves_list = re.findall(moves_pattern, input)
    return SGF(initial_whites=aw_list, initial_blacks=ab_list, moves=moves_list)

  @staticmethod
  def to_base64(sgf: "SGF", black_first: bool, key: str = "101222") -> str:
    if black_first:
      payload = repr([sgf.initial_blacks, sgf.initial_whites])
    else:
      payload = repr([sgf.initial_whites, sgf.initial_blacks])
    enc = [chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(payload)]
    return base64.b64encode("".join(enc).encode("utf-8")).decode("utf-8")

def _detect_key(b64: str) -> str:
  """Return the XOR key used to encode b64, falling back to '101222'."""
  raw = base64.b64decode(b64).decode("utf-8")
  for key in ["101222", "101333"]:
    dec = "".join(chr(ord(raw[i]) ^ ord(key[i % len(key)])) for i in range(len(raw)))
    try:
      eval(dec)
      return key
    except Exception:
      continue
  return "101222"

def to_goban_coordinate(move: str) -> str:
    cols = list("ABCDEFGHJKLMNOPQRST")
    col = cols[ord(move[0]) - ord('a')]
    row = 19 - ord(move[1]) + ord('a')
    return f"{col}{row}"

def from_goban_coordinate(move: str) -> str:
    cols = list("ABCDEFGHJKLMNOPQRST")
    col = chr(ord('a') + cols.index(move[0]))
    row = chr(ord('a') + 19 - int(move[1:]))
    return f"{col}{row}"

def _compute_outputs(path: str) -> tuple[str, str, str]:
  """Return (sgf, gnos, solution) strings that process_one would write for path."""
  assert(path.endswith(".json"))
  with open(path) as file:
    input_json = json.load(file)

  def best_answer_key(x: dict[str, Any]) -> tuple:
      return (
          x["ty"] == 1,
          x["st"] == 2,
          x["ok_count"],
          -x["error_count"],
          -x["bad_count"],
          str(x),
      )

  best_answer = max(input_json["answers"], key=best_answer_key, default={"pts": []})
  best_answer_moves = [x["p"] for x in best_answer["pts"]]

  theproblem = SGF.from_base64(input_json["c"], input_json["blackfirst"])
  if input_json["xv"] % 3 != 0:
    theproblem = theproblem.sflip()
  theproblem = evolve(theproblem, moves=best_answer_moves)
  permutations = [
    p := theproblem,
    (p := p.rotate()),
    (p := p.rotate()),
    (p := p.rotate()),
    (p := p.sflip()),
    (p := p.rotate()),
    (p := p.rotate()),
    (p := p.rotate()),
  ]
  # last key component is a tie breaker
  theproblem = min(permutations, key=lambda x: (x.height, x.width, sorted(x.initial_blacks)))
  if input_json["status"] == 1:
    solution_moves = "eliminated"
  else:
    solution_moves = " ".join(map(to_goban_coordinate, theproblem.moves))

  return (
    theproblem.to_sgf() + "\n",
    theproblem.to_gnos() + "\n",
    solution_moves + "\n",
  )


def process_one(path: str) -> None:
  sgf, gnos, solution = _compute_outputs(path)
  stem = path.removesuffix(".json")
  with open(f"{stem}.sgf", "w") as file:
    file.write(sgf)
  with open(f"{stem}.gnos", "w") as file:
    file.write(gnos)
  with open(f"{stem}.solution", "w") as file:
    file.write(solution)


def update_json_from_sgf(json_path: str, sgf_path: str) -> bool:
  """Update board position and solution in json_path from sgf_path.

  The SGF must have been produced by process_one (i.e. already in canonical
  orientation). Returns True if the file was written.  Idempotent: a second
  call with the same SGF leaves the JSON unchanged.
  """
  with open(json_path) as f:
    data = json.load(f)
  with open(sgf_path) as f:
    new_sgf = SGF.from_sgf(f.read())

  new_status = 2 if new_sgf.moves else 1

  # If the JSON already produces the correct canonical SGF, "c" and answers are
  # already semantically correct (possibly in a different orientation/format).
  try:
    expected_sgf, _, _ = _compute_outputs(json_path)
    board_and_moves_unchanged = (expected_sgf == new_sgf.to_sgf() + "\n")
  except Exception:
    board_and_moves_unchanged = False

  needs_write = False
  if not board_and_moves_unchanged:
    board_for_c = new_sgf.sflip() if data["xv"] % 3 != 0 else new_sgf
    key = _detect_key(data["c"]) if data.get("c") else "101222"
    data["c"] = SGF.to_base64(board_for_c, data["blackfirst"], key)
    new_pts = [{"p": m, "c": ""} for m in new_sgf.moves]
    data["answers"] = [{
      "id": 0, "st": 2, "ty": 1, "nu": 0,
      "username": "", "userid": 0,
      "pts": new_pts, "v": 0,
      "ok_count": 1, "change_count": 0, "bad_count": 0, "error_count": 0,
      "created": 0,
    }]
    needs_write = True
  if data.get("status") != new_status:
    data["status"] = new_status
    needs_write = True

  if not needs_write:
    return False
  with open(json_path, "w") as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    f.write("\n")
  return True


def update_sgf_from_solution(sgf_path: str, solution_path: str) -> bool:
  """Replace moves in sgf_path with those from solution_path. Returns True if changed."""
  with open(sgf_path) as f:
    sgf = SGF.from_sgf(f.read())
  with open(solution_path) as f:
    solution = f.read().strip()

  new_moves = [] if solution == "eliminated" else [from_goban_coordinate(m) for m in solution.split()]

  if sgf.moves == new_moves:
    return False

  with open(sgf_path, "w") as f:
    f.write(evolve(sgf, moves=new_moves).to_sgf() + "\n")
  return True


def update_from_git(commit: str | None = None) -> None:
  """Update .json files whose .sgf counterpart changed in git.

  Without a commit, uses all SGFs that differ from HEAD (staged or unstaged).
  With a commit hash/ref, uses SGFs changed by that specific commit.
  """
  if commit:
    cmd = ["git", "diff", "--name-only", f"{commit}^!"]
  else:
    cmd = ["git", "diff", "--name-only", "HEAD"]
  result = subprocess.run(cmd, capture_output=True, text=True, check=True)
  sgf_paths = [p for p in result.stdout.splitlines() if p.endswith(".sgf")]
  if not sgf_paths:
    print("No changed .sgf files found.")
    return
  for sgf_path in sgf_paths:
    json_path = sgf_path.removesuffix(".sgf") + ".json"
    if not os.path.exists(json_path):
      print(f"skip {sgf_path}: no matching .json", file=sys.stderr)
      continue
    changed = update_json_from_sgf(json_path, sgf_path)
    print(f"{'updated' if changed else 'unchanged'}: {json_path}")


def check_coherence(json_path: str) -> bool:
  """Warn if .sgf/.gnos/.solution don't match what the .json would generate.

  Returns True if all three files are present and coherent.
  """
  expected_sgf, expected_gnos, expected_solution = _compute_outputs(json_path)
  stem = json_path.removesuffix(".json")
  ok = True
  for ext, expected in [
    (".sgf", expected_sgf),
    (".gnos", expected_gnos),
    (".solution", expected_solution),
  ]:
    path = stem + ext
    if not os.path.exists(path):
      print(f"MISSING  {path}")
      ok = False
      continue
    with open(path) as f:
      actual = f.read()
    if actual != expected:
      print(f"MISMATCH {path}")
      ok = False
  return ok


def check_from_git(commit: str | None = None) -> bool:
  """Check coherence for all problems touched by changed files in git.

  Discovers stems from any changed .json/.sgf/.gnos/.solution file and runs
  check_coherence on each. Returns True if all are coherent.
  """
  if commit:
    cmd = ["git", "diff", "--name-only", f"{commit}^!"]
  else:
    cmd = ["git", "diff", "--name-only", "HEAD"]
  result = subprocess.run(cmd, capture_output=True, text=True, check=True)
  stems = set()
  for p in result.stdout.splitlines():
    for ext in (".json", ".sgf", ".gnos", ".solution"):
      if p.endswith(ext):
        stems.add(p.removesuffix(ext))
        break
  if not stems:
    print("No changed problem files found.")
    return True
  all_ok = True
  for stem in sorted(stems):
    json_path = stem + ".json"
    if not os.path.exists(json_path):
      print(f"skip {stem}: no .json", file=sys.stderr)
      continue
    if not check_coherence(json_path):
      all_ok = False
  return all_ok


def reconcile_one(json_path: str) -> bool:
  """Run the full reconciliation pipeline and verify consistency.

  Steps: .solution -> .sgf (moves), .sgf -> .json, .json -> all files.
  Warns if .sgf, .gnos, or .solution differ after regeneration. Returns True if consistent.
  """
  stem = json_path.removesuffix(".json")
  sgf_path = stem + ".sgf"
  gnos_path = stem + ".gnos"
  solution_path = stem + ".solution"

  update_sgf_from_solution(sgf_path, solution_path)

  with open(sgf_path) as f: sgf_before = f.read()
  with open(gnos_path) as f: gnos_before = f.read()
  with open(solution_path) as f: solution_before = f.read()

  update_json_from_sgf(json_path, sgf_path)
  process_one(json_path)

  ok = True
  with open(sgf_path) as f:
    if f.read() != sgf_before:
      print(f"WARNING: {sgf_path} changed after regeneration")
      ok = False
  with open(gnos_path) as f:
    if f.read() != gnos_before:
      print(f"WARNING: {gnos_path} changed after regeneration")
      ok = False
  with open(solution_path) as f:
    if f.read() != solution_before:
      print(f"WARNING: {solution_path} changed after regeneration")
      ok = False
  return ok


def reconcile_from_git(commit: str | None = None) -> bool:
  """Reconcile all problems touched by changed files in git. Returns True if all consistent."""
  if commit:
    cmd = ["git", "diff", "--name-only", f"{commit}^!"]
  else:
    cmd = ["git", "diff", "--name-only", "HEAD"]
  result = subprocess.run(cmd, capture_output=True, text=True, check=True)
  stems = set()
  for p in result.stdout.splitlines():
    for ext in (".json", ".sgf", ".gnos", ".solution"):
      if p.endswith(ext):
        stems.add(p.removesuffix(ext))
        break
  if not stems:
    print("No changed problem files found.")
    return True
  all_ok = True
  for stem in sorted(stems):
    json_path = stem + ".json"
    if not os.path.exists(json_path):
      print(f"skip {stem}: no .json", file=sys.stderr)
      continue
    if not reconcile_one(json_path):
      all_ok = False
  return all_ok


def main(args: list[str]) -> None:
  if args and args[0] == "--update-from-git":
    update_from_git(args[1] if len(args) > 1 else None)
  elif args and args[0] == "--check":
    ok = True
    for path in args[1:]:
      if not check_coherence(path):
        ok = False
    sys.exit(0 if ok else 1)
  elif args and args[0] == "--check-from-git":
    ok = check_from_git(args[1] if len(args) > 1 else None)
    sys.exit(0 if ok else 1)
  elif args and args[0] == "--reconcile":
    ok = True
    for path in args[1:]:
      if not reconcile_one(path):
        ok = False
    sys.exit(0 if ok else 1)
  elif args and args[0] == "--reconcile-from-git":
    ok = reconcile_from_git(args[1] if len(args) > 1 else None)
    sys.exit(0 if ok else 1)
  else:
    for path in args:
      process_one(path)

if __name__ == "__main__":
  main(sys.argv[1:])
