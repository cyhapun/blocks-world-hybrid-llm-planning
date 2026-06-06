(define (problem bw_easy_004)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table a)
    (on_table c)
    (on b a)
    (clear b)
    (clear c)
    (handempty)
  )

  (:goal
    (on c b)
  )
)
