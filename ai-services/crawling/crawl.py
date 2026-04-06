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


def _normalize_locality(raw_locality: str) -> str:
	value = raw_locality.strip()
	if not value:
		return "Khác"

	normalized = re.sub(r"\s+", " ", value).strip()
	upper = normalized.upper().replace(".", "")

	if "HCM" in upper or "HO CHI MINH" in upper:
		return "HCM"
	if "HUE" in upper or "HUẾ" in upper:
		return "Huế"
	if "DA NANG" in upper or "ĐÀ NẴNG" in upper:
		return "Đà Nẵng"

	return normalized


def _extract_locality(theatre_name: str) -> str:
	match = re.search(r"\(([^)]+)\)", theatre_name)
	if match:
		return _normalize_locality(match.group(1))

	# Fallback: if no parenthesis, try to infer from full theatre text.
	return _normalize_locality(theatre_name)


def _iter_dict_nodes(data: Any) -> Iterable[dict[str, Any]]:
	if isinstance(data, dict):
		yield data
		for value in data.values():
			yield from _iter_dict_nodes(value)
	elif isinstance(data, list):
		for item in data:
			yield from _iter_dict_nodes(item)


def _extract_movie_name(next_data: dict[str, Any], soup: BeautifulSoup) -> str:
	page_props = next_data.get("props", {}).get("pageProps", {})
	if isinstance(page_props, dict):
		movie_data = page_props.get("movieData") or page_props.get("movie")
		if isinstance(movie_data, dict):
			for key in ("name_vn", "name", "title", "movie_name_vn", "movie_name_en"):
				value = movie_data.get(key)
				if isinstance(value, str) and value.strip():
					return value.strip()

	if soup.title and soup.title.string:
		return soup.title.string.strip()

	return "Unknown Movie"


def _extract_movie_description(next_data: dict[str, Any], soup: BeautifulSoup) -> str:
	page_props = next_data.get("props", {}).get("pageProps", {})
	if isinstance(page_props, dict):
		movie_data = page_props.get("movieData") or page_props.get("movie")
		if isinstance(movie_data, dict):
			for key in ("description", "description_vn", "description_en", "content"):
				value = movie_data.get(key)
				if isinstance(value, str) and value.strip():
					return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)

	meta = soup.find("meta", attrs={"name": "description"})
	if meta and isinstance(meta.get("content"), str) and meta.get("content").strip():
		return meta.get("content").strip()

	return ""


def _extract_movie_poster(next_data: dict[str, Any], soup: BeautifulSoup) -> str:
	page_props = next_data.get("props", {}).get("pageProps", {})
	if isinstance(page_props, dict):
		movie_data = page_props.get("movieData") or page_props.get("movie")
		if isinstance(movie_data, dict):
			for key in (
				"thumbnail",
				"image",
				"poster",
				"poster_url",
				"cover",
				"banner",
			):
				value = movie_data.get(key)
				if isinstance(value, str) and value.strip():
					return value.strip()

	og_image = soup.find("meta", attrs={"property": "og:image"})
	if og_image and isinstance(og_image.get("content"), str) and og_image.get("content").strip():
		return og_image.get("content").strip()

	return ""


def _parse_rows_from_next_data(next_data: dict[str, Any]) -> List[tuple[str, str, str]]:
	results: List[tuple[str, str, str]] = []
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
			results.append((theatre, normalized_day, normalized_time))

	return results


def _group_schedules(
	rows: List[tuple[str, str, str]], movie_name: str
) -> List[dict[str, Any]]:
	grouped: dict[str, dict[str, dict[str, List[str]]]] = {}

	for theatre, day, time in rows:
		locality = _extract_locality(theatre)
		grouped.setdefault(locality, {})
		grouped[locality].setdefault(theatre, {})
		grouped[locality][theatre].setdefault(day, [])

		if time not in grouped[locality][theatre][day]:
			grouped[locality][theatre][day].append(time)

	result: List[dict[str, Any]] = []
	for locality, theatres in grouped.items():
		theatre_items: List[dict[str, Any]] = []
		for theatre_name, day_map in theatres.items():
			schedule = [
				{
					"day": day,
					"showtimes": sorted(times),
				}
				for day, times in day_map.items()
			]

			theatre_items.append(
				{
					"theatre": theatre_name,
					"movies": [
						{
							"movie_name": movie_name,
							"schedule": schedule,
						}
					],
				}
			)

		result.append(
			{
				"locality": locality,
				"theatres": theatre_items,
			}
		)

	return result


def get_movie_schedules(movie_url: str, debug_html: bool = False) -> dict[str, Any]:
	"""
	Crawl movie page and return grouped schedules by:
	Locality -> Theatre -> Movie Name -> Showtimes (grouped by day)
	"""
	response = requests.get(movie_url, timeout=20)
	response.raise_for_status()
	response.encoding = response.apparent_encoding or response.encoding

	if debug_html:
		print(response.text)

	soup = BeautifulSoup(response.text, "html.parser")

	next_data_script = soup.find("script", id="__NEXT_DATA__")
	if not next_data_script or not next_data_script.string:
		return {
			"movie": {
				"title": "Unknown Movie",
				"description": "",
				"poster_url": "",
			},
			"schedules": [],
		}

	try:
		next_data = json.loads(next_data_script.string)
	except json.JSONDecodeError:
		return {
			"movie": {
				"title": "Unknown Movie",
				"description": "",
				"poster_url": "",
			},
			"schedules": [],
		}

	movie_name = _extract_movie_name(next_data, soup)
	movie_description = _extract_movie_description(next_data, soup)
	movie_poster = _extract_movie_poster(next_data, soup)
	rows = _parse_rows_from_next_data(next_data)
	return {
		"movie": {
			"title": movie_name,
			"description": movie_description,
			"poster_url": movie_poster,
		},
		"schedules": _group_schedules(rows, movie_name),
	}


def get_movie_schedule(movie_url: str) -> dict[str, Any]:
	"""Backward-compatible alias."""
	return get_movie_schedules(movie_url)

