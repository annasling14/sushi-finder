SELECT
    s.location,
    COUNT(*) AS results,
    ROUND(AVG(sn.adjusted_score), 2) AS avg_score
FROM snapshots sn
JOIN searches s ON s.id = sn.search_id
GROUP BY s.location
ORDER BY avg_score DESC;

SELECT
    r.name,
    COUNT(DISTINCT sn.search_id) AS times_seen,
    MAX(sn.review_count) - MIN(sn.review_count) AS review_growth
FROM restaurants r
JOIN snapshots sn ON sn.place_id = r.place_id
GROUP BY r.place_id
ORDER BY times_seen DESC;

