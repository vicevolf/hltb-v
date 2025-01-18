# HLTB Unofficial API - Vercel

An **unofficial API** for [HowLongToBeat](https://howlongtobeat.com), built with Python Flask on Vercel. It is designed to help dedicated gamers explore and track game completion times, enhancing their overall gaming experience.

---

## Usage

### Search Endpoint  

**GET** `/api/search`  

- **Parameters:**  
  - `key` (**required**): Your API key.  
  - `game` (**required**): The game name to search.  

- **Example:**
  
```
GET https://example.vercel.app/api/search?key=YOUR_API_KEY&game=Outer Wilds
```

- **Response:**  

```json
{
  "game_name": "Outer Wilds",
  "similarity": 1,
  "source": "api",
  "times": {
    "completionist": 27.84,
    "main_extra": 22.31,
    "main_story": 16.96
  }
}
```

---

## Configuration

### Environment Variables  

- `API_KEY` (**required**): A secure, complex key for request authentication.  
- `ALLOWED_DOMAINS` (*optional*): Restricts requests to specific domains (default: `*` for all).  

### Caching

A short-lived cache minimizes duplicate requests.  

---

## Error Codes  

- **400**: Invalid or missing game name.  
- **401**: Unauthorized (invalid API key or domain restriction).  
- **404**: Game not found or no match.  
- **500**: Server error.  

If you encounter an unknown exception, try updating `howlongtobeatpy` in the `requirements.txt` file to the latest version.

---

## Based On  

Built with the [`HowLongToBeat-PythonAPI`](https://github.com/ScrappyCocco/HowLongToBeat-PythonAPI) by **@ScrappyCocco**.  

---

## Note  

This is an **unofficial** API. Respect [HowLongToBeat](https://howlongtobeat.com) and its rules to avoid overloading their service.