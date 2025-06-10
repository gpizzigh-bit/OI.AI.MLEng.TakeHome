function extract_prediction_0(tag, timestamp, record)
    if record["predictions"] and type(record["predictions"]) == "table" then
        local p0 = record["predictions"][1]
        if p0 then
        record["pred0_class"]      = p0["class_name"]
        record["pred0_confidence"] = p0["confidence"]
        end
    end
    return 1, timestamp, record
    end
