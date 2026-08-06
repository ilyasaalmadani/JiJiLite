from core.turn_guard import is_stale_plan

assert is_stale_plan(
    "apa itu demokrasi",
    {
        "resolved_query":
        "Apa saja wisata di Kabupaten Karanganyar?"
    },
)

assert not is_stale_plan(
    "apa itu demokrasi",
    {
        "resolved_query":
        "Jelaskan pengertian demokrasi."
    },
)

assert not is_stale_plan(
    "wisata",
    {
        "resolved_query":
        "Apa saja wisata di Kabupaten Karanganyar?"
    },
)

print("✓ Turn Isolation Guard berhasil")
