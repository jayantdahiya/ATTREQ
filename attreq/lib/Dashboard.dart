import 'package:attreq/Animations/FadeAnimationDashboard.dart';
import 'package:flutter/material.dart';
import 'package:smooth_star_rating/smooth_star_rating.dart';

void main() => runApp(MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(fontFamily: 'Nunito'),
      home: HomePage(),
    ));

class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage>
    with SingleTickerProviderStateMixin {
  late PageController _pageController;
  int totalPage = 3;

  void _onScroll() {}

  @override
  void initState() {
    _pageController = PageController(
      initialPage: 0,
    )..addListener(_onScroll);

    super.initState();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  var rating = 3.0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PageView(
        controller: _pageController,
        children: <Widget>[
          makePage(
              page: 1,
              image: 'assets/Collections/collection1.png',
              title: 'Outfit 1',
              description:
                  'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque nec placerat dolor, ac cursus mauris. Interdum et malesuada fames ac ante ipsum primis in faucibus. '),
          makePage(
              page: 2,
              image: 'assets/Collections/collection2.png',
              title: 'Outfit 2',
              description:
                  'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque nec placerat dolor, ac cursus mauris. Interdum et malesuada fames ac ante ipsum primis in faucibus.'),
          makePage(
              page: 3,
              image: 'assets/Collections/collection3.png',
              title: 'Outfit 3',
              description:
                  'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque nec placerat dolor, ac cursus mauris. Interdum et malesuada fames ac ante ipsum primis in faucibus.'),
          // makePage(
          //   page: 4,
          //   image: 'assets/images/four.jpg',
          //   title: 'Savannah',
          //   description: "Savannah, with its Spanish moss, Southern accents and creepy graveyards, is a lot like Charleston, South Carolina. But this city about 100 miles to the south has an eccentric streak."
          // ),
        ],
      ),
    );
  }

  Widget makePage({image, title, description, page}) {
    return Container(
      decoration: BoxDecoration(
          image: DecorationImage(image: AssetImage(image), fit: BoxFit.cover)),
      child: Container(
        decoration: BoxDecoration(
            gradient: LinearGradient(begin: Alignment.bottomRight, stops: [
          0.3,
          0.9
        ], colors: [
          Colors.black.withOpacity(.9),
          Colors.black.withOpacity(.2),
        ])),
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                SizedBox(
                  height: 40,
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: <Widget>[
                    FadeAnimation(
                        2,
                        Text(
                          page.toString(),
                          style: TextStyle(
                              color: Colors.white,
                              fontSize: 30,
                              fontWeight: FontWeight.bold),
                        )),
                    Text(
                      '/' + totalPage.toString(),
                      style: TextStyle(color: Colors.white, fontSize: 15),
                    )
                  ],
                ),
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      FadeAnimation(
                          1,
                          Text(
                            title,
                            style: TextStyle(
                                color: Colors.white,
                                fontSize: 50,
                                height: 1.2,
                                fontWeight: FontWeight.bold),
                          )),
                      SizedBox(
                        height: 20,
                      ),
                      FadeAnimation(
                          1.5,
                          Row(
                            children: <Widget>[
                              // Container(
                              //   margin: EdgeInsets.only(right: 3),
                              //   child: Icon(
                              //     Icons.star,
                              //     color: Colors.yellow,
                              //     size: 15,
                              //   ),
                              // ),
                              // Container(
                              //   margin: EdgeInsets.only(right: 3),
                              //   child: Icon(
                              //     Icons.star,
                              //     color: Colors.yellow,
                              //     size: 15,
                              //   ),
                              // ),
                              // Container(
                              //   margin: EdgeInsets.only(right: 3),
                              //   child: Icon(
                              //     Icons.star,
                              //     color: Colors.yellow,
                              //     size: 15,
                              //   ),
                              // ),
                              // Container(
                              //   margin: EdgeInsets.only(right: 3),
                              //   child: Icon(
                              //     Icons.star,
                              //     color: Colors.yellow,
                              //     size: 15,
                              //   ),
                              // ),
                              // Container(
                              //   margin: EdgeInsets.only(right: 5),
                              //   child: Icon(
                              //     Icons.star,
                              //     color: Colors.grey,
                              //     size: 15,
                              //   ),
                              // ),
                              // Text(
                              //   '4.0',
                              //   style: TextStyle(color: Colors.white70),
                              // ),
                              //   Text(
                              //     '(2300)',
                              //     style: TextStyle(
                              //         color: Colors.white38, fontSize: 12),
                              //   )
                            ],
                          )),
                      SizedBox(
                        height: 5,
                      ),
                      FadeAnimation(
                          2,
                          Padding(
                            padding: const EdgeInsets.only(right: 50),
                            child: Text(
                              description,
                              style: TextStyle(
                                  color: Colors.white.withOpacity(.7),
                                  height: 1.9,
                                  fontSize: 15),
                            ),
                          )),
                      SizedBox(
                        height: 20,
                      ),
                      // FadeAnimation(
                      //     2.5,
                      //     Text(
                      //       "I'll wear this!",
                      //       style: TextStyle(color: Colors.white),
                      //     )),
                      FadeAnimation(
                          2.5,
                          SmoothStarRating(
                            rating: rating,
                            isReadOnly: false,
                            size: 30,
                            color: Colors.yellow,
                            borderColor: Colors.yellow,
                            filledIconData: Icons.star,
                            halfFilledIconData: Icons.star_half,
                            defaultIconData: Icons.star_border,
                            starCount: 5,
                            allowHalfRating: false,
                            spacing: 2.0,
                          )),
                      SizedBox(
                        height: 30,
                      ),
                    ],
                  ),
                )
              ]),
        ),
      ),
    );
  }
}
