FLEX_MSG_WEDDING_INFO = {
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "日期",
            "flex": 1
          },
          {
            "type": "text",
            "text": "📅 2024/12/08 (日)",
            "flex": 2
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "地點",
            "flex": 1,
          },
          {
            "type": "text",
            "text": "📍 孫立人將軍官邸",
            "flex": 2,
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "時間",
            "flex": 1
          },
          {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "🍸 10:30 雞尾酒派對",
              },
              {
                "type": "text",
                "text": "💍 11:00 戶外證婚",
              },
              {
                "type": "text",
                "text": "🍽️ 12:18 喜宴開始",
              }
            ],
            "flex": 2,
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "button",
            "action": {
              "type": "uri",
              "label": "邀請函",
              "uri": "https://forms.gle/pbjZzYWJsP6EfHEe9"
            }
          },
          {
            "type": "button",
            "action": {
              "type": "uri",
              "label": "地圖",
              "uri": "https://maps.app.goo.gl/nB27agtpkfzGtzwT9"
            }
          }
        ]
      }
    ],
    "spacing": "xl"
  }
}

FLEX_MSG_GREETING = {
  "type": "bubble",
  "hero": {
    "type": "image",
    "url": "https://stimim-wedding-bot.de.r.appspot.com/static/banner.png",
    "size": "full",
    "aspectRatio": "3:2",
    "aspectMode": "cover"
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "「我們要結婚了！」",
            "weight": "bold",
            "margin": "xs"
          },
          {
            "type": "text",
            "text": "從虛擬網友正式升級人生隊友! ",
            "offsetTop": "none"
          }
        ]
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "舉辦婚禮的起心動念，"
          },
          {
            "type": "text",
            "text": "是希望這一天盈滿歡樂與暖意，"
          },
          {
            "type": "text",
            "text": "與生命歷程裡的每位夥伴，"
          },
          {
            "type": "text",
            "text": "一同慶賀美好的日子！"
          }
        ]
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "誠摯邀請您，參與我們的 Big Day"
          },
          {
            "type": "text",
            "text": "再請於 10/13 (六) 前完成表單填寫"
          },
          {
            "type": "text",
            "text": "期待當天與您們相聚！"
          }
        ]
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "一起來玩吧！🙌 ",
            "weight": "bold"
          }
        ]
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "🙋‍♂️🙋‍♀️總召：陳韋翰 / 吳家慧"
          }
        ]
      }
    ],
    "spacing": "xl"
  },
  "footer": {
    "type": "box",
    "layout": "horizontal",
    "contents": [
      {
        "type": "button",
        "action": {
          "type": "uri",
          "label": "邀請函",
          "uri": "https://forms.gle/pbjZzYWJsP6EfHEe9"
        }
      },
      {
        "type": "button",
        "action": {
          "type": "message",
          "label": "婚禮資訊",
          "text": "!婚禮資訊"
        }
      }
    ]
  }
}
