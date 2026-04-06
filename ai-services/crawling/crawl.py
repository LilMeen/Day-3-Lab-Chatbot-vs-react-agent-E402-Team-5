from __future__ import annotations

import json
import re
from typing import Any, Iterable, List

import requests
from bs4 import BeautifulSoup


def _normalize_day(raw_day: str) -> str:
	match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", raw_day)
	return match.group(1) if match else raw_day.strip()


def _normalize_time(raw_time: str) -> str:
	match = re.search(r"(\d{1,2}:\d{2})", raw_time)
	return match.group(1) if match else raw_time.strip()


def _iter_dict_nodes(data: Any) -> Iterable[dict[str, Any]]:
	if isinstance(data, dict):
		yield data
		for value in data.values():
			yield from _iter_dict_nodes(value)
	elif isinstance(data, list):
		for item in data:
			yield from _iter_dict_nodes(item)


def _parse_from_next_data(next_data: dict[str, Any]) -> List[List[str]]:
	results: List[List[str]] = []
	seen: set[tuple[str, str, str]] = set()

	for node in _iter_dict_nodes(next_data):
		day = node.get("date")
		times = node.get("times")

		if not isinstance(day, str) or not isinstance(times, list):
			continue

		normalized_day = _normalize_day(day)
		for item in times:
			if not isinstance(item, dict):
				continue

			raw_time = str(item.get("time") or "").strip()
			normalized_time = _normalize_time(raw_time)
			if not normalized_time:
				continue

			theatre = (
				str(item.get("theater_name_vn") or "").strip()
				or str(item.get("theater_name_en") or "").strip()
			)

			key = (theatre, normalized_day, normalized_time)
			if key in seen:
				continue

			seen.add(key)
			results.append([theatre, normalized_day, normalized_time])

	return results


def get_movie_schedules(movie_url: str, debug_html: bool = False) -> List[List[str]]:
	"""
	Crawl movie page and return schedules as:
	[[Theatre, Day, Time], ...]
	"""
	response = requests.get(movie_url, timeout=20)
	response.raise_for_status()
	response.encoding = response.apparent_encoding or response.encoding

	if debug_html:
		print(response.text)

	soup = BeautifulSoup(response.text, "html.parser")

	next_data_script = soup.find("script", id="__NEXT_DATA__")
	if not next_data_script or not next_data_script.string:
		return []

	try:
		next_data = json.loads(next_data_script.string)
	except json.JSONDecodeError:
		return []

	return _parse_from_next_data(next_data)


def get_movie_schedule(movie_url: str) -> List[List[str]]:
	"""Backward-compatible alias."""
	return get_movie_schedules(movie_url)

