from tools.base import register_tool


def smart_followup(context_summary: str, followup_type: str = "clarify_preference") -> dict:
    """Generate a contextual follow-up to maintain conversation flow."""

    templates = {
        "confirm_booking": {
            "intent": "xac_nhan_dat_ve",
            "message": f"Dua tren thong tin truoc do: {context_summary}\n\nBan co muon toi xac nhan dat ve khong? Vui long xac nhan cac thong tin sau:\n- Phim va suat chieu\n- Loai ghe\n- So luong ve",
            "suggested_actions": ["Xac nhan dat ve", "Thay doi suat chieu", "Xem khuyen mai truoc"]
        },
        "clarify_preference": {
            "intent": "lam_ro_so_thich",
            "message": f"Toi can them thong tin de giup ban tot hon. {context_summary}\n\nBan co the cho toi biet them ve:\n- Ngay gio ban muon xem?\n- Loai phong chieu uu tien (Standard, IMAX, 4DX, VIP)?\n- Ngan sach cho ve?",
            "suggested_actions": ["Chon ngay gio", "Chon loai phong", "Dat ngan sach"]
        },
        "suggest_alternative": {
            "intent": "goi_y_thay_the",
            "message": f"Dua tren yeu cau cua ban: {context_summary}\n\nToi co mot so goi y thay the:\n- Xem phim khac cung the loai\n- Doi sang suat chieu khac\n- Thu rap khac voi gia tot hon",
            "suggested_actions": ["Xem phim khac", "Doi suat chieu", "Doi rap"]
        }
    }

    if followup_type not in templates:
        return {
            "status": "error",
            "message": f"Loai followup '{followup_type}' khong hop le. Chon: confirm_booking, clarify_preference, suggest_alternative"
        }

    template = templates[followup_type]
    return {
        "status": "success",
        "followup_type": followup_type,
        "intent": template["intent"],
        "message": template["message"],
        "suggested_actions": template["suggested_actions"]
    }


register_tool(
    name="smart_followup",
    description="Tao cau hoi/goi y theo ngu canh de duy tri hoi thoai. Dung khi can xac nhan, lam ro y dinh, hoac goi y thay the.",
    parameters={
        "context_summary": {"type": "string", "description": "Tom tat ngu canh hoi thoai hien tai", "required": True},
        "followup_type": {"type": "string", "description": "Loai followup: confirm_booking, clarify_preference, suggest_alternative", "required": True}
    },
    function=smart_followup
)
