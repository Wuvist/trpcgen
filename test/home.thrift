namespace java home
namespace objc home

include "base.thrift"

struct TPic {
	3: required string hyperLink;		// 广告链接
}

struct TBanner {
	1: required base.TPromotionAd ad;	// 广告名
	2: required list<base.TPromotionAd> oldAds;		// 广告图url
	3: required string hyperLink;		// 广告链接
	4: required TPic onePic;		// 广告链接
	5: required list<TPic> morePics;		// 广告链接
}

service Utility {
	list<base.TPromotionAd> GetAds(),
}
