# discount_config.py
# Lululemon折扣配置
DISCOUNT_CONFIG = {
    "明洞乐天": {
        "description": "明洞乐天免税店专属优惠",
        "options": [
            {
                "name": "5%折扣券",
                "type": "pre_tax_percent",
                "rate": 0.05,
                "rule": "总价5%折扣（税前优惠）"
            },
            {
                "name": "银联满10万减7500",
                "type": "pre_tax_fixed",
                "threshold": 100000,
                "amount": 7500,
                "once_only": True,
                "rule": "单笔支付满10万韩元减7500（仅限一次）"
            }
        ]
    },
    "新世界": {
        "description": "明洞/江南/釜山新世界优惠",
        "options": [
            {
                "name": "会员卡5%折扣",
                "type": "pre_tax_percent",
                "rate": 0.05,
                "rule": "需出示会员卡，总价5%折扣（税前优惠）"
            },
            {
                "name": "银联满10万减1万",
                "type": "pre_tax_fixed",
                "threshold": 100000,
                "amount": 10000,
                "once_only": True,
                "rule": "单笔支付满10万韩元减1万（仅限一次）"
            },
            {
                "name": "银联阶梯赠券",
                "type": "post_tax_tiered",
                "tiers": [
                    {"threshold": 200000, "amount": 10000},
                    {"threshold": 400000, "amount": 20000},
                    {"threshold": 600000, "amount": 30000}
                ],
                "rule": "税后总价满20/40/60万赠1/2/3万商品券"
            }
        ]
    },
    "韩国电话注册": {
        "description": "韩国电话注册新会员优惠",
        "options": [
            {
                "name": "新会员5%折扣",
                "type": "pre_tax_percent",
                "rate": 0.05,
                "rule": "需韩国电话注册新会员，总价5%折扣（税前优惠）"
            }
        ]
    },
    "乐天/新世界奥莱": {
        "description": "奥特莱斯专属优惠",
        "options": [
            {
                "name": "银联满5万10%折扣",
                "type": "pre_tax_capped",
                "threshold": 50000,
                "rate": 0.10,
                "cap": 10000,
                "rule": "银联消费满5万韩元享10%折扣，最高减1万韩元"
            }
        ]
    }
}
